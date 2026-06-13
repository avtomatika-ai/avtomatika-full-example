import asyncio
import os
import pytest
import aiohttp
import subprocess
import time

API_URL = os.environ.get("API_URL", "http://localhost:8080")
CLIENT_TOKEN = "user_token_vip"
# We use the docker service name since orchestrator runs in docker
WEBHOOK_RECEIVER_URL = "http://webhook-receiver:5000/webhook"


async def run_scenario(session, name, data):
    headers = {"X-Client-Token": CLIENT_TOKEN}
    payload = {"initial_data": data, "webhook_url": WEBHOOK_RECEIVER_URL}

    print(f"\n[SCENARIO] 🚀 Starting: {name}", flush=True)
    async with session.post(
        f"{API_URL}/api/v1/submit/full_showcase", json=payload, headers=headers
    ) as resp:
        if resp.status not in [201, 202]:
            txt = await resp.text()
            print(f"  ❌ Failed to submit: HTTP {resp.status} - {txt}", flush=True)
            return None
        res = await resp.json()
        job_id = res["job_id"]
        print(f"  🆔 Job ID: {job_id}", flush=True)

    for i in range(200):  # 100 seconds max
        await asyncio.sleep(0.5)
        async with session.get(
            f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
        ) as resp:
            state = await resp.json()
            status = state.get("status")
            if not status:
                # Log for debugging if status is missing
                print(f"DEBUG: Missing status in response: {state}")
                continue

            step = state.get("current_state", "N/A")

            # Transparency: check workers status during wait
            if i % 10 == 0:
                async with session.get(
                    f"{API_URL}/api/v1/workers", headers=headers
                ) as w_resp:
                    workers = await w_resp.json()
                    w_info = ", ".join(
                        [
                            f"{w.get('worker_id', 'unknown')}({w.get('status', 'offline')})"
                            for w in workers
                        ]
                    )

                    print(
                        f"    ⏳ [{i * 0.5}s] Status: {status} | Step: {step} | Workers: [{w_info}]",
                        flush=True,
                    )

            # Handle Human-in-the-loop
            if status == "waiting_for_human":
                async with session.post(
                    f"{API_URL}/_public/webhooks/approval/{job_id}",
                    json={"decision": "approved"},
                    headers=headers,
                ) as approve_resp:
                    if approve_resp.status == 200:
                        print(f"    ✅ Approval sent for job {job_id}")

            if status in ["finished", "failed", "quarantined", "cancelled"]:
                print(f"  🏁 Finished with status: {status}", flush=True)
                return state
    return None


@pytest.mark.asyncio
async def test_infrastructure_ready():
    async with aiohttp.ClientSession() as session:
        for _ in range(30):
            try:
                async with session.get(f"{API_URL}/_public/status") as resp:
                    if resp.status == 200:
                        break

            except Exception:
                pass
            await asyncio.sleep(1)
        else:
            pytest.fail("Infrastructure not ready (Orchestrator /status timed out)")

        # Wait for 3+ workers
        headers = {"X-Client-Token": CLIENT_TOKEN}
        for _ in range(120):
            try:
                async with session.get(
                    f"{API_URL}/api/v1/workers", headers=headers
                ) as resp:
                    if resp.status == 200:
                        all_workers = await resp.json()
                        now = int(time.time())
                        idle_workers = [
                            w
                            for w in all_workers
                            if w.get("status") == "idle"
                            and w.get("timestamp", 0) >= now - 30
                        ]
                        if len(idle_workers) >= 3:
                            return
            except Exception:
                pass
            await asyncio.sleep(1)
        pytest.fail("Workers did not register and become idle in time")


@pytest.mark.asyncio
async def test_all_scenarios():
    async with aiohttp.ClientSession() as session:
        res = await run_scenario(session, "Standard", {"path": "test.mp4"})
        assert res is not None and res["status"] == "finished"


@pytest.mark.asyncio
async def test_security_spoofing_rejected():
    """
    Test that an unauthenticated or improperly signed worker event is rejected.
    """
    async with aiohttp.ClientSession() as session:
        # 1. Try to send an event with a fake worker ID but NO token
        payload = {
            "event_type": "spoofed_event",
            "worker_id": "fake-worker",
            "origin_worker_id": "fake-worker",
            "payload": {"data": "hack"},
            "timestamp": time.time(),
        }
        async with session.post(f"{API_URL}/_worker/events", json=payload) as resp:
            # Should be 401 Unauthorized or 403 Forbidden because of missing token
            assert resp.status in [401, 403]

        # 2. Try to send an event with a VALID worker ID but WRONG token
        headers = {"X-Worker-Token": "wrong-token"}
        payload["worker_id"] = "gpu-worker-01"
        payload["origin_worker_id"] = "gpu-worker-01"
        async with session.post(
            f"{API_URL}/_worker/events", json=payload, headers=headers
        ) as resp:
            # Should be 401 or 403
            assert resp.status in [401, 403]

        # 3. Try to send an event with a VALID token but WRONG HMAC signature (Zero Trust)
        headers = {"X-Worker-Token": "super-secret-gpu-worker-token"}
        payload["security"] = {
            "signature": "fake-signature",
            "signer_id": "gpu-worker-01",
        }
        async with session.post(
            f"{API_URL}/_worker/events", json=payload, headers=headers
        ) as resp:
            # Since we implemented verify_signature properly now, this MUST fail with 403 (Zero Trust violation)
            assert resp.status == 403
            txt = await resp.text()
            assert "signature" in txt.lower()


@pytest.mark.asyncio
async def test_webhook_delivery_verification():
    time.sleep(2)
    cmd = "docker compose logs webhook-receiver --tail 50"
    logs = subprocess.check_output(cmd, shell=True).decode()
    assert "WEBHOOK:" in logs
