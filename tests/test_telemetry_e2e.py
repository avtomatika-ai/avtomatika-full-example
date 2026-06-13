import asyncio
import os

import aiohttp
import pytest

# Configuration
API_URL = os.environ.get("API_URL", "http://localhost:8080")
CLIENT_TOKEN = "user_token_vip"


async def verify_history_trace_integrity(session, job_id, headers):
    """
    Verifies that all events for a job in history have the same Trace ID.
    Supports retries for async storage consistency.
    """
    for _ in range(5):
        async with session.get(
            f"{API_URL}/api/v1/jobs/{job_id}/history", headers=headers
        ) as resp:
            history = await resp.json()
            if not history:
                await asyncio.sleep(1)
                continue

            trace_ids = set()
            for event in history:
                # 1. Check direct field
                t_id = event.get("trace_id")
                if t_id:
                    trace_ids.add(t_id)
                    continue

                # 2. Check root tracing_context
                root_tc = event.get("tracing_context", {})
                if root_tc and "traceparent" in root_tc:
                    trace_id = root_tc["traceparent"].split("-")[1]
                    trace_ids.add(trace_id)
                    continue

                # 3. Check tracing_context in snapshot (fallback)
                snapshot = event.get("context_snapshot") or {}
                tc = snapshot.get("tracing_context", {})
                if tc and "traceparent" in tc:
                    trace_id = tc["traceparent"].split("-")[1]
                    trace_ids.add(trace_id)

            if len(trace_ids) == 0:
                await asyncio.sleep(1)
                continue

            if len(trace_ids) > 1:
                return False, f"Multiple trace IDs found: {trace_ids}"

            return True, list(trace_ids)[0]
    return False, "No trace IDs found in history after retries"


@pytest.mark.asyncio
async def test_telemetry_parallel_execution():
    """
    Verifies that multiple tasks running in parallel maintain the same Trace ID.
    """
    async with aiohttp.ClientSession() as session:
        headers = {"X-Client-Token": CLIENT_TOKEN}
        payload = {
            "initial_data": {"count": 3, "base_name": "parallel_test"},
        }

        # Use a blueprint that triggers parallel execution
        async with session.post(
            f"{API_URL}/api/v1/submit/full_showcase", json=payload, headers=headers
        ) as resp:
            job_id = (await resp.json())["job_id"]

        print(f"Testing Parallel Telemetry for Job ID: {job_id}")

        # Wait for completion (handling approval if needed)
        status = "pending"
        for _ in range(60):
            async with session.get(
                f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
            ) as resp:
                data = await resp.json()
                status = data.get("status")
                if status == "waiting_for_human":
                    await session.post(
                        f"{API_URL}/_public/webhooks/approval/{job_id}",
                        json={"decision": "approved"},
                        headers=headers,
                    )
                if status in ["finished", "failed"]:
                    break
            await asyncio.sleep(1)

        assert status == "finished"

        success, result = await verify_history_trace_integrity(session, job_id, headers)
        assert success, result
        print(f"✅ Parallel Telemetry Verified. Trace ID: {result}")


@pytest.mark.asyncio
async def test_telemetry_sub_blueprint_propagation():
    """
    Verifies that Trace ID is propagated through sub-blueprints (Parent -> Child).
    """
    async with aiohttp.ClientSession() as session:
        headers = {"X-Client-Token": CLIENT_TOKEN}
        payload = {"initial_data": {"path": "sub_test.mp4"}}

        # Submit parent job
        async with session.post(
            f"{API_URL}/api/v1/submit/full_showcase", json=payload, headers=headers
        ) as resp:
            parent_job_id = (await resp.json())["job_id"]

        print(f"Testing Hierarchical Telemetry for Parent ID: {parent_job_id}")

        # Wait for completion and find child job ID
        child_job_id = None
        for _ in range(60):
            async with session.get(
                f"{API_URL}/api/v1/jobs/{parent_job_id}", headers=headers
            ) as resp:
                data = await resp.json()
                status = data.get("status")

                # Check for child job in state
                if "child_job_id" in data:
                    child_job_id = data["child_job_id"]

                if status == "waiting_for_human":
                    await session.post(
                        f"{API_URL}/_public/webhooks/approval/{parent_job_id}",
                        json={"decision": "approved"},
                        headers=headers,
                    )
                if status == "finished":
                    break
            await asyncio.sleep(1)

        assert child_job_id is not None, "Child job ID not found in parent state"
        print(f"Found Child Job ID: {child_job_id}")

        # 1. Verify Parent Trace
        p_success, p_trace = await verify_history_trace_integrity(
            session, parent_job_id, headers
        )
        assert p_success, p_trace

        # 2. Verify Child Trace (Must be SAME as Parent)
        c_success, c_trace = await verify_history_trace_integrity(
            session, child_job_id, headers
        )
        assert c_success, c_trace

        assert p_trace == c_trace, (
            f"Trace ID mismatch! Parent: {p_trace}, Child: {c_trace}"
        )
        print(f"✅ Hierarchical Telemetry Verified. Unified Trace ID: {p_trace}")
