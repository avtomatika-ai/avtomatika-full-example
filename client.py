"""
Avtomatika Example Client
"""

import asyncio
import json
import logging
from datetime import datetime
from os import environ
from sys import stdout

import aiohttp

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("client")

API_URL = environ.get("ORCHESTRATOR_URL", "http://localhost:8080")
CLIENT_TOKEN = environ.get("CLIENT_TOKEN", "user_token_vip")
BLUEPRINT = "full_showcase"

SCENARIOS = {
    "1": {
        "name": "Standard Flow (Transcode -> Parallel Analysis -> Sub-Blueprint -> S3 Report)",
        "data": {"path": "/videos/movie.mp4", "quality": "high"},
    },
    "2": {
        "name": "Smart Dispatching (Use Hot Skills Target)",
        "data": {"path": "/videos/ai_gen.mp4", "use_hot_skills": True},
    },
    "3": {
        "name": "Error Handling (Simulate Transient Error)",
        "data": {"path": "/videos/test.mp4", "trigger": "transient"},
    },
    "4": {
        "name": "Interactive Cancellation (Demo WebSocket Interruption)",
        "data": {"path": "/videos/cancel_me.mp4", "is_cancellation_demo": True},
    },
}


async def main():
    print("\n--- Avtomatika HLN Interactive Demo ---")
    for key, scenario in SCENARIOS.items():
        print(f"{key}. {scenario['name']}")

    choice = input("\nSelect a scenario [1]: ") or "1"
    selected = SCENARIOS.get(choice, SCENARIOS["1"])

    async with aiohttp.ClientSession() as session:
        headers = {"X-Client-Token": CLIENT_TOKEN}
        payload = {
            "initial_data": selected["data"],
            "webhook_url": "http://localhost:5000/webhook",
        }

        print(f"\n🔌 Connecting to {API_URL}...")
        try:
            async with session.post(
                f"{API_URL}/api/submit/{BLUEPRINT}", json=payload, headers=headers
            ) as resp:
                if resp.status not in [201, 202]:
                    print(f"❌ Failed to create job: {resp.status} {await resp.text()}")
                    return

                job_info = await resp.json()
                job_id = job_info["job_id"]
                print(f"✅ Job created! ID: {job_id}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            return

        print(
            "\n[Monitoring] Waiting for updates. Press Ctrl+C to cancel the job manually."
        )
        seen_events = set()

        try:
            while True:
                async with session.get(
                    f"{API_URL}/api/v1/jobs/{job_id}", headers=headers
                ) as resp:
                    if resp.status != 200:
                        print(f"\n❌ Error fetching status: {resp.status}")
                        break
                    data = await resp.json()
                    status = data["status"]

                async with session.get(
                    f"{API_URL}/api/v1/jobs/{job_id}/history", headers=headers
                ) as resp:
                    if resp.status == 200:
                        history = await resp.json()
                        for event in history:
                            event_type = event.get("event_type", "")
                            if event_type.startswith("worker_event:"):
                                ts_val = event.get("timestamp", 0)
                                event_key = f"{event_type}_{ts_val}"
                                if event_key not in seen_events:
                                    ts_str = datetime.fromtimestamp(ts_val).strftime(
                                        "%H:%M:%S"
                                    )
                                    payload_data = event.get(
                                        "context_snapshot", {}
                                    ).get("payload", {})
                                    print(
                                        f"\n  [{ts_str}] 🔔 EVENT: {event_type[13:]} -> {payload_data}"
                                    )
                                    seen_events.add(event_key)

                if status in ["finished", "failed", "quarantined", "cancelled"]:
                    print(f"\n\n🏁 Final Status: {status.upper()}")
                    if status == "finished":
                        result = data.get("state_history") or data.get("result")
                        print(f"🎉 Result: {json.dumps(result, indent=2)}")
                    elif status == "cancelled":
                        print("🛑 Job was successfully cancelled.")
                    else:
                        print(f"⚠️ Error: {data.get('error_message')}")
                    break

                progress = data.get("progress", 0.0)
                bar_len = 20
                filled_len = int(bar_len * progress)
                bar = "█" * filled_len + "░" * (bar_len - filled_len)

                stdout.write(
                    f"\rStatus: {status.ljust(12)} | [{bar}] {progress * 100:5.1f}%"
                )
                stdout.flush()

                await asyncio.sleep(0.5)
        except KeyboardInterrupt:
            print(f"\n\n🛑 User interruption. Attempting to CANCEL job {job_id}...")
            async with session.post(
                f"{API_URL}/api/v1/jobs/{job_id}/cancel", headers=headers
            ) as resp:
                if resp.status == 200:
                    print("✅ Cancellation command sent to Orchestrator.")
                else:
                    print(f"❌ Failed to cancel: {resp.status} {await resp.text()}")

            await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Client stopped.")
