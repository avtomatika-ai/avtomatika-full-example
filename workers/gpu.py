"""Avtomatika: Modernized GPU Worker"""

import asyncio
import logging
from os import environ

from avtomatika_worker import Worker, TaskFiles
from avtomatika_worker.config import WorkerConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gpu_worker")

config = WorkerConfig()
config.COST_PER_SKILL = {"transcode_video": 0.001, "generate_video_report": 0.0001}
config.S3_DEFAULT_BUCKET = environ.get("S3_DEFAULT_BUCKET", "avtomatika-payloads")
config.S3_ENDPOINT_URL = environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
config.WORKER_ID = environ.get("WORKER_ID")
config.WORKER_TOKEN = environ.get("WORKER_TOKEN")

# Increase resources to exceed default task requirements
config.RESOURCES = {"properties": {"cpu_cores": 8, "ram_gb": 16}}

worker = Worker(
    worker_type="gpu",
    config=config,
)

# Use hot cache to target this specific worker from blueprints
worker._hot_cache.add("video-preset-v1")


@worker.skill(name="transcode_video", type="transcode_video", version="1.0.0")
async def transcode_video(
    job_id: str,
    task_id: str,
    send_progress,
    send_event,
    task_files: TaskFiles,
    **kwargs,
):
    logger.info(f"[{job_id}] GPU: Starting transcoding...")

    # 1. Report Progress
    for i in range(1, 4):
        await asyncio.sleep(0.5)
        await send_progress(task_id, job_id, i / 3.0, f"Transcoding chunk {i}/3")

    # 2. Emit Custom Worker Event (hardware monitoring)
    await send_event("gpu_thermal_status", {"temp": 65.5, "fan_speed": "auto"})

    # 3. Use TaskFiles for S3 Payload Offloading
    filename = "transcoded_video.txt"
    await task_files.write(filename, f"Video content for job {job_id}")
    result_path = await task_files.path_to(filename)

    return {
        "status": "success",
        "data": {
            "output_file": result_path,
            "bitrate": "5Mbps",
        },
    }


@worker.skill(
    name="generate_video_report", type="generate_video_report", version="1.0.0"
)
async def generate_video_report(**kwargs):
    return {"status": "success"}


@worker.on_command("drain")
async def handle_drain(command):
    from rxon.constants import WORKER_STATUS_DRAINING

    logger.info("DRAIN command received. Preparing to stop...")
    # This will trigger the stop in the next polling iteration
    worker._config.EXTRA_CAPABILITIES["status"] = WORKER_STATUS_DRAINING
    # Trigger a heartbeat update immediately
    worker._schedule_heartbeat_debounce()


if __name__ == "__main__":
    config.WORKER_PORT = int(environ.get("WORKER_PORT", 8083))
    worker.run_with_health_check()
