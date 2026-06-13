"""
Avtomatika: Full Feature Demonstration
"""

import logging
import redis.asyncio as redis
from os import environ
from asyncio import CancelledError, Event, run

from avtomatika import OrchestratorEngine
from avtomatika.config import Config
from avtomatika.storage.redis import RedisStorage

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    environ["GLOBAL_WORKER_TOKEN"] = "super-secret-worker-token"

    config = Config()
    config.API_PORT = 8080

    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        password=getattr(config, "REDIS_PASSWORD", None),
        decode_responses=False,
        socket_timeout=60.0,
        socket_keepalive=True,
        health_check_interval=30,
    )

    storage = RedisStorage(redis_client)
    engine = OrchestratorEngine(config=config, storage=storage)

    # Explicitly register all blueprints before setup
    from blueprints import (
        main_bp,
        metadata_enrichment_bp,
        maintenance_bp,
        media_cleanup_bp,
    )

    engine.register_blueprint(main_bp)
    engine.register_blueprint(metadata_enrichment_bp)
    engine.register_blueprint(maintenance_bp)
    engine.register_blueprint(media_cleanup_bp)

    engine.setup()

    from avtomatika.worker_config_loader import load_worker_configs_to_redis
    from avtomatika.client_config_loader import load_client_configs_to_redis

    if config.WORKERS_CONFIG_PATH:
        await load_worker_configs_to_redis(
            storage, config.WORKERS_CONFIG_PATH, config.WORKER_AUTH_MODE
        )

    await load_client_configs_to_redis(storage, "example_clients.toml")

    try:
        await engine.start()
        logger.info("🚀 Avtomatika Orchestrator is running!")
        logger.info(f"API available at http://{config.API_HOST}:{config.API_PORT}")

        stop_event = Event()
        await stop_event.wait()

    except (KeyboardInterrupt, CancelledError):
        pass
    except Exception as e:
        logger.exception(f"Critical error during orchestrator startup: {e}")
    finally:
        logger.info("Shutting down orchestrator...")
        await engine.stop()
        await redis_client.close()


if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt:
        pass
