"""Avtomatika: Unreliable CPU Worker"""

import asyncio
import logging
from os import environ
from pydantic import BaseModel, Field

from avtomatika_worker import Worker, SkillInfo
from avtomatika_worker.config import WorkerConfig

# Configure basic logging
logging.basicConfig(level=logging.INFO)


class AnalysisParams(BaseModel):
    """Pydantic model for task parameters."""

    resource_id: str | None = Field(None, description="The ID of the file to analyze")


# Configure the worker
config = WorkerConfig()
config.S3_DEFAULT_BUCKET = environ.get("S3_DEFAULT_BUCKET", "avtomatika-payloads")
config.S3_ENDPOINT_URL = environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
config.WORKER_ID = environ.get("WORKER_ID")
config.WORKER_TOKEN = environ.get("WORKER_TOKEN")
config.COST_PER_SKILL = {"analyze_file": 0.0001}
config.RESOURCES = {"properties": {"cpu_cores": 8, "ram_gb": 16}}

# Define skills explicitly
skills = [
    SkillInfo(name="analyze_file", type="analyze_file", version="1.0.0"),
]

# Create a worker instance
worker = Worker(
    worker_type="cpu_worker_unreliable",
    config=config,
)
worker._supported_skills = skills


@worker.skill(name="analyze_file", version="1.0.0")
async def analyze_file(params: AnalysisParams, task_id: str, job_id: str, **kwargs):
    """An unreliable handler."""
    logging.info(f"Task {task_id}: starting unreliable analysis")
    await asyncio.sleep(0.5)
    return {"status": "success", "data": {"analysis": {"status": "partial"}}}


if __name__ == "__main__":
    config.WORKER_PORT = int(environ.get("WORKER_PORT", 8085))
    worker.run_with_health_check()
