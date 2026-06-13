import asyncio
import os
import sys
import time

import aiohttp
import pytest

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8080")
CLIENT_TOKEN = os.environ.get("CLIENT_TOKEN", "user_token_vip")


@pytest.mark.asyncio
async def test_integration_full_flow():
    """
    Modular E2E Integration Test:
    1. Worker Registration Verification
    2. Job Submission (via Blueprint API)
    3. State Machine Transitions (Human -> Parallel -> Sub-blueprint)
    4. Result Aggregation
    """
    async with aiohttp.ClientSession() as session:
        headers = {"X-Client-Token": CLIENT_TOKEN}

        # 1. VERIFY WORKERS
        workers = []
        for _ in range(60):
            async with session.get(
                f"{API_URL}/api/v1/workers", headers=headers
            ) as resp:
                assert resp.status == 200
                all_workers = await resp.json()
                now = int(time.time())
                workers = [
                    w
                    for w in all_workers
                    if (w.get("status") == "idle" or w.get("status") == "active")
                    and w.get("timestamp", 0) >= now - 60
                ]
                if len(workers) >= 3:
                    break
            await asyncio.sleep(1)
        assert len(workers) >= 3, (
            f"Expected at least 3 active workers, found {len(workers)}"
        )

        # 2. SUBMIT JOB
        payload = {
            "initial_data": {
                "path": "/videos/movie.mp4",
                "quality": "high",
                "use_hot_skills": True,
            }
        }

        # Blueprint endpoints are registered with /api/ prefix
        # for explicit endpoints.
        async with session.post(
            f"{API_URL}/api/v1/submit/full_showcase", json=payload, headers=headers
        ) as resp:
            assert resp.status in [201, 202], (
                f"Failed to submit job: {resp.status} {await resp.text()}"
            )
            job_id = (await resp.json())["job_id"]
        print(f"Test Job ID: {job_id}")

        # 3. POLL FOR STATUS & HUMAN APPROVAL
        status = "pending"
        for _ in range(60):
            async with session.get(
                f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
            ) as resp:
                assert resp.status == 200
                data = await resp.json()
                status = data.get("status")
                print(f"Polling Job {job_id}: status={status}")

                if status == "waiting_for_human":
                    print(
                        f"✅ Job {job_id} is waiting for human approval. Sending 'approved' decision..."
                    )
                    async with session.post(
                        f"{API_URL}/_public/webhooks/approval/{job_id}",
                        json={"decision": "approved"},
                        headers=headers,
                    ) as decide_resp:
                        assert decide_resp.status == 200
                        print("🚀 Approval sent!")

                if status in ["finished", "failed", "quarantined", "cancelled"]:
                    break
            await asyncio.sleep(2)

        assert status == "finished", (
            f"Job failed with status: {status}. Error: {data.get('error_message')}"
        )

        # 4. VERIFY FINAL STATE & AGGREGATION
        async with session.get(
            f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
        ) as resp:
            state = await resp.json()

        # In new version, context is flattened in the job state or in state_history
        # Aggregator updates often land in 'initial_data' for subsequent steps
        context = state.get("state_history", {})
        initial_data = state.get("initial_data", {})
        if not context:
            context = state

        # Check for either the custom summary or raw aggregation results
        # In new version, aggregation results are often merged into 'result'
        result = state.get("result", {})
        has_aggregation = (
            "analysis_summary" in context
            or "aggregation_results" in context
            or "is_aggregated" in context
            or (isinstance(result, dict) and "analysis_summary" in result)
            or "analysis_summary" in initial_data
        )
        assert has_aggregation, (
            f"Fan-in aggregation failed. Context keys: {list(context.keys())}, InitialData keys: {list(initial_data.keys())}, Result keys: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}"
        )

        # Verify sub-blueprint interactions (Multiple child jobs expected)
        async with session.get(
            f"{API_URL}/api/v1/jobs/{job_id}/history", headers=headers
        ) as resp:
            history = await resp.json()

        child_jobs = []
        for event in history:
            snapshot = event.get("context_snapshot", {})
            if snapshot.get("child_job_id"):
                child_jobs.append(snapshot.get("child_job_id"))

        # Remove duplicates
        child_jobs = list(set(child_jobs))

        print(f"Child job IDs executed: {child_jobs}")
        assert len(child_jobs) >= 2, (
            f"Expected at least 2 sub-jobs (metadata_enrichment and media_cleanup), found {len(child_jobs)}"
        )

        print("✅ Modular E2E Integration Test PASSED (Multiple Sub-Jobs Verified)!")
