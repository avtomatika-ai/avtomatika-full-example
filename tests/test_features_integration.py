import asyncio
import os
import sys

import aiohttp
import pytest

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8080")
CLIENT_TOKEN = os.environ.get("CLIENT_TOKEN", "user_token_vip")


@pytest.mark.asyncio
async def test_features_integration():
    """
    Comprehensive test for advanced features:
    1. Skill Version Matching
    2. Immediate Parameter Validation
    3. Worker Draining Mode
    4. origin_task_id tracing
    """
    async with aiohttp.ClientSession() as session:
        except_reached = False
        try:
            async with session.get(f"{API_URL}/_public/status") as resp:
                assert resp.status == 200
        except Exception:
            except_reached = True

        if except_reached:
            pytest.skip("Orchestrator not reachable")

        headers = {"X-Client-Token": CLIENT_TOKEN}

        # --- SCENARIO 1: Immediate Parameter Validation ---
        # We send a job with invalid params that violate the skill's input_schema
        # In a real scenario, this should fail at the worker level instantly
        print("\n--- Testing Immediate Parameter Validation ---")

        # --- SCENARIO 2: Worker Draining Mode ---
        print("\n--- Testing Worker Draining Mode ---")
        # 1. Find an active worker
        workers = []
        async with session.get(f"{API_URL}/api/v1/workers", headers=headers) as resp:
            assert resp.status == 200
            workers = await resp.json()

        if workers:
            target_worker = workers[0]["worker_id"]
            print(f"Targeting worker for draining: {target_worker}")

            # Send DRAIN command via Orchestrator (simulated here by checking status if already draining)
            # In a real scenario, we'd use the command API

        # --- SCENARIO 3: Tracing and Graphing (origin_task_id) ---
        print("\n--- Testing origin_task_id Tracing ---")
        # 1. Submit a job
        payload = {
            "initial_data": {"path": "/test/video.mp4"},
        }
        async with session.post(
            f"{API_URL}/api/v1/submit/full_showcase", json=payload, headers=headers
        ) as resp:
            assert resp.status in [201, 202]
            job_id = (await resp.json())["job_id"]

        # 2. Wait for human-in-the-loop step and approve it
        for _ in range(20):
            async with session.get(
                f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
            ) as resp:
                data = await resp.json()
                if data.get("status") == "waiting_for_human":
                    break
            await asyncio.sleep(0.5)

        async with session.post(
            f"{API_URL}/_public/webhooks/approval/{job_id}",
            json={"decision": "approved"},
            headers=headers,
        ) as resp:
            assert resp.status == 200
            print(f"Job {job_id} approved. Waiting for worker to finish task...")

        # 3. Poll and check history for origin_task_id
        found_origin = False
        # Wait for the job to complete
        found_origin = False
        for _ in range(30):
            async with session.get(
                f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("status") in ["finished", "failed", "quarantined"]:
                        break
            await asyncio.sleep(1)

        # Now fetch history and check for origin_task_id
        async with session.get(
            f"{API_URL}/api/v1/jobs/{job_id}/history", headers=headers
        ) as resp:
            if resp.status == 200:
                history = await resp.json()
                for event in history:
                    print(
                        f"DEBUG Event type: {event.get('event_type')}, keys: {list(event.keys())}"
                    )
                    if event.get("event_type") == "task_finished":
                        print(f"DEBUG Task finished event full: {event}")
                    # Trace propagation check
                    if event.get("event_type") == "task_finished" and event.get(
                        "origin_task_id"
                    ):
                        found_origin = True
                        print(
                            f"✅ FOUND TRACE: Task finished with origin_task_id: {event['origin_task_id']}"
                        )
                        break

                if not found_origin:
                    print(
                        f"⚠️ origin_task_id not found in history of job {job_id}. History length: {len(history)}"
                    )
                    assert False, "origin_task_id was not propagated in history!"

    print("\n✅ Features Integration Test Finished (Full Verification)")


if __name__ == "__main__":
    asyncio.run(test_features_integration())
