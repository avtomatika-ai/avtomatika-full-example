"""Avtomatika: Secure mTLS Worker Example"""

import asyncio
import logging
from os import environ, path
from pydantic import BaseModel, Field

from avtomatika_worker import Worker
from avtomatika_worker.config import WorkerConfig

# Configure basic logging
logging.basicConfig(level=logging.INFO)


class SecureAnalysisParams(BaseModel):
    """Pydantic model for secure task parameters."""

    resource_id: str | None = Field(
        None, description="The ID of the file to analyze securely"
    )


# Configure the worker
config = WorkerConfig()
config.WORKER_ID = environ.get("WORKER_ID", "secure-worker-01")

# mTLS Configuration (Paths to certificates)
# These would typically be provided via environment variables in a real deployment
# config.TLS_CA_PATH = environ.get("TLS_CA_PATH", "certs/ca.pem")
# config.TLS_CERT_PATH = environ.get("TLS_CERT_PATH", "certs/worker.crt")
# config.TLS_KEY_PATH = environ.get("TLS_KEY_PATH", "certs/worker.key")

config.S3_DEFAULT_BUCKET = environ.get("S3_DEFAULT_BUCKET", "avtomatika-payloads")
config.S3_ENDPOINT_URL = environ.get("S3_ENDPOINT_URL", "http://localhost:9000")
config.COST_PER_SKILL = {"secure_analyze": 0.0005}
config.RESOURCES = {"properties": {"cpu_cores": 4, "ram_gb": 8, "secure_enclave": True}}

# Create a worker instance
# The Worker SDK will automatically initialize SSLContext if TLS paths are provided in config
worker = Worker(
    worker_type="secure_worker",
    config=config,
)


@worker.skill(name="secure_analyze", version="1.0.0", type="secure_analyze")
async def secure_analyze(
    params: SecureAnalysisParams, task_id: str, job_id: str, **kwargs
):
    """A secure handler for the 'secure_analyze' task."""
    logging.info(f"Task {task_id}: performing secure analysis")
    # Simulate work
    await asyncio.sleep(1.0)
    return {
        "status": "success",
        "data": {"result": "Securely analyzed", "confidentiality": "high"},
        "metadata": {"encryption": "aes-256-gcm"},
    }


if __name__ == "__main__":
    # Check if we have certs and log it
    if config.TLS_CERT_PATH and path.exists(config.TLS_CERT_PATH):
        logging.info(
            f"🚀 Starting Secure Worker with mTLS using {config.TLS_CERT_PATH}"
        )
    else:
        logging.info(
            "🚀 Starting Secure Worker (mTLS not configured, falling back to Token/Mixed mode)"
        )

    config.WORKER_PORT = int(environ.get("WORKER_PORT", 8085))
    worker.run_with_health_check()
