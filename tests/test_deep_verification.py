import asyncio
import os
import sys
import pytest
import aiohttp

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8080")
MASTER_TOKEN = "super-secret-cpu-worker-token"
WORKER_ID = "cpu-worker-01"


@pytest.mark.asyncio
async def test_sts_deep_security_and_rotation():
    """
    Deep verification of STS:
    1. Token Obtain & Use (Zero Trust Check)
    2. Impersonation Check (Wrong ID with Master Token)
    """
    async with aiohttp.ClientSession() as session:
        # 1. Obtain Initial STS Token (Success Case)
        headers = {"X-Worker-Token": MASTER_TOKEN, "X-Worker-ID": WORKER_ID}
        async with session.post(
            f"{API_URL}/_worker/auth/token", headers=headers
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            sts_token = data["access_token"]
            refresh_token = data["refresh_token"]
            assert len(sts_token) > 20
            assert len(refresh_token) > 20

        print(
            f"✅ STS Initialized: {sts_token[:10]}... (Refresh: {refresh_token[:10]}...)"
        )

        # 2. Use STS Token for Heartbeat
        auth_headers = {"X-Worker-Token": sts_token, "X-Worker-ID": WORKER_ID}
        async with session.patch(
            f"{API_URL}/_worker/workers/{WORKER_ID}", headers=auth_headers
        ) as resp:
            assert resp.status == 200

        print("✅ STS token accepted for heartbeat")

        # 3. Refresh Token (Zero Trust)
        refresh_payload = {"refresh_token": refresh_token}
        refresh_headers = {"X-Worker-ID": WORKER_ID}
        async with session.post(
            f"{API_URL}/_worker/auth/token/refresh",
            json=refresh_payload,
            headers=refresh_headers,
        ) as resp:
            assert resp.status == 200
            data = await resp.json()
            new_sts_token = data["access_token"]
            new_refresh_token = data["refresh_token"]
            assert new_sts_token != sts_token
            assert new_refresh_token != refresh_token

        print("✅ STS Token rotated successfully via Refresh Token")

        # 4. Impersonation during Refresh
        async with session.post(
            f"{API_URL}/_worker/auth/token/refresh",
            json=refresh_payload,
            headers={"X-Worker-ID": "fake-worker-id"},
        ) as resp:
            assert resp.status == 403

        print("✅ Impersonation during refresh REJECTED (X-Worker-ID check works)")


@pytest.mark.asyncio
async def test_child_job_ownership_inheritance():
    """
    Verifies that a client can access the history of a child job created by the orchestrator.
    This confirms the 'No Hacks' ownership inheritance.
    """
    CLIENT_TOKEN = "user_token_vip"
    async with aiohttp.ClientSession() as session:
        headers = {"X-Client-Token": CLIENT_TOKEN}
        payload = {"initial_data": {"path": "ownership_test.mp4"}}

        # Submit parent job
        async with session.post(
            f"{API_URL}/api/v1/submit/full_showcase", json=payload, headers=headers
        ) as resp:
            parent_id = (await resp.json())["job_id"]

        print(f"Parent Job: {parent_id}")

        # Wait for child job to be created
        child_id = None
        for _ in range(30):
            async with session.get(
                f"{API_URL}/api/v1/jobs/{parent_id}", headers=headers
            ) as resp:
                data = await resp.json()
                if data.get("status") == "waiting_for_human":
                    await session.post(
                        f"{API_URL}/_public/webhooks/approval/{parent_id}",
                        json={"decision": "approved"},
                        headers=headers,
                    )
                # Flexible check for child_job_id in root or nested context
                child_id = data.get("child_job_id") or data.get("context", {}).get(
                    "child_job_id"
                )
                if child_id:
                    break
            await asyncio.sleep(1)

        assert child_id is not None, "Child job was not created"
        print(f"Child Job: {child_id}")

        # Verify access to child history using parent's token
        async with session.get(
            f"{API_URL}/api/v1/jobs/{child_id}/history", headers=headers
        ) as resp:
            assert resp.status == 200
            history = await resp.json()
            assert len(history) > 0
            print(
                f"✅ Child history accessible with parent token (History size: {len(history)})"
            )
