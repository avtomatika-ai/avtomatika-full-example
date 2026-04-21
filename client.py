"""
Avtomatika Example Client

This script demonstrates how an external application interacts with the Orchestrator:
1. Authenticates using a Client Token.
2. Creates a new Job.
3. Polls for status updates and displays a real-time Progress Bar.
"""

import asyncio
import json
import logging
from datetime import datetime
from os import environ
from sys import stdout

import aiohttp

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("client")

# Configuration
API_URL = environ.get("ORCHESTRATOR_URL", "http://localhost:8080")
CLIENT_TOKEN = environ.get("CLIENT_TOKEN", "user_token_vip")
BLUEPRINT = "full_showcase"

SCENARIOS = {
    "1": {
        "name": "Standard Flow (Transcode -> Parallel Analysis -> Sub-Blueprint -> S3 Report)",
        "data": {"path": "/videos/movie.mp4", "quality": "high"},
    },
    "2": {
        "name": "Smart Dispatching (Use Hot Cache Target)",
        "data": {"path": "/videos/ai_gen.mp4", "use_hot_cache": True},
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
            "webhook_url": "http://localhost:8000/webhook",
        }

        print(f"\n🔌 Connecting to {API_URL}...")
        try:
            # The API endpoint is defined in the blueprint itself
            async with session.post(
                f"{API_URL}/api/v1/submit/{BLUEPRINT}", json=payload, headers=headers
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
                    data = await resp.json()
                    status = data["status"]

                    # Show new Ghost/Worker events
                    for event in data.get("events", []):
                        event_key = f"{event['event_type']}_{event.get('timestamp')}"
                        if event_key not in seen_events:
                            ts = datetime.fromtimestamp(
                                event.get("timestamp", 0)
                            ).strftime("%H:%M:%S")
                            print(
                                f"\n  [{ts}] 🔔 EVENT: {event['event_type']} -> {event['payload']}"
                            )
                            seen_events.add(event_key)

                    if status in ["finished", "failed", "quarantined", "cancelled"]:
                        print(f"\n\n🏁 Final Status: {status.upper()}")
                        if status == "finished":
                            print(
                                f"🎉 Result: {json.dumps(data.get('state_history', {}), indent=2)}"
                            )
                        elif status == "cancelled":
                            print("🛑 Job was successfully cancelled.")
                        else:
                            print(f"⚠️ Error: {data.get('error_message')}")
                        break

                    # Progress Bar
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

            # Wait a bit to show the final status
            await asyncio.sleep(2)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Client stopped.")
