import logging
from avtomatika import Blueprint, ActionFactory

logger = logging.getLogger("blueprints.media")
blueprint = Blueprint(name="media_cleanup")


@blueprint.handler("start", is_start=True)
async def start(job_id: str, actions: ActionFactory):
    logger.info(f"[{job_id}] MEDIA-CLEANUP: Starting cleanup process.")
    actions.go_to("finished")
    return actions


@blueprint.handler("finished", is_end=True)
async def finished(job_id: str):
    logger.info(f"[{job_id}] MEDIA-CLEANUP: Process finished.")
