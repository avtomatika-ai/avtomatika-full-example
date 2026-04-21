"""
Avtomatika: Full Feature Demonstration (Minimal Beta 20)
"""

import logging
import redis.asyncio as redis
from os import environ
from asyncio import CancelledError, Event, run

from avtomatika import OrchestratorEngine
from avtomatika.storage.redis import RedisStorage
from config import config

logger = logging.getLogger("orchestrator")


async def main():
    """
    Main entry point for the demonstration.
    """
    log_level_str = environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if log_level == logging.DEBUG:
        logging.getLogger("avtomatika").setLevel(logging.DEBUG)
        logging.getLogger("rxon").setLevel(logging.DEBUG)

    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        decode_responses=False,
    )

    storage = RedisStorage(redis_client)
    engine = OrchestratorEngine(config=config, storage=storage)

    # Explicitly register all blueprints to avoid discovery issues
    from blueprints import main_bp, metadata_enrichment_bp, maintenance_bp

    engine.register_blueprint(main_bp)
    engine.register_blueprint(metadata_enrichment_bp)
    engine.register_blueprint(maintenance_bp)

    try:
        # Start the engine (API server and background executors)
        await engine.start()
        logger.info("🚀 Avtomatika Orchestrator is running!")
        logger.info(f"API available at http://{config.API_HOST}:{config.API_PORT}")

        stop_event = Event()
        await stop_event.wait()

    except (KeyboardInterrupt, CancelledError):
        logger.info("Shutting down...")
    finally:
        logger.info("Shutting down orchestrator...")
        await engine.stop()
        await redis_client.close()


if __name__ == "__main__":
    try:
        run(main())
    except KeyboardInterrupt:
        pass
