"""Avtomatika: Reliable CPU Worker"""

import asyncio
import logging
from os import environ
from pydantic import BaseModel, Field

from avtomatika_worker import Worker
from avtomatika_worker.config import WorkerConfig

logging.basicConfig(level=logging.INFO)


class AnalysisParams(BaseModel):
    resource_id: str | None = Field(None, description="The ID of the file to analyze")


config = WorkerConfig()
config.S3_DEFAULT_BUCKET = environ.get("S3_DEFAULT_BUCKET", "avtomatika-payloads")
config.S3_ENDPOINT_URL = environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
config.WORKER_ID = environ.get("WORKER_ID", "")
config.WORKER_TOKEN = environ.get("WORKER_TOKEN", "")
config.COST_PER_SKILL = {"analyze_file": 0.0001}
config.RESOURCES = {"properties": {"cpu_cores": 8, "ram_gb": 16}}

worker = Worker(
    worker_type="cpu_worker",
    config=config,
)


@worker.skill(name="analyze_file", version="1.0.0", type="analyze_file")
async def analyze_file(params: AnalysisParams, task_id: str, job_id: str, **kwargs):
    logging.info(f"Task {task_id}: starting 'analyze_file'")
    await asyncio.sleep(0.5)
    return {"status": "success", "data": {"analysis": {"status": "ok"}}}


if __name__ == "__main__":
    config.WORKER_PORT = int(environ.get("WORKER_PORT", 8084))
    worker.run_with_health_check()
