import logging
from avtomatika import Blueprint
from avtomatika.context import ActionFactory

logger = logging.getLogger("blueprints.sub")
metadata_enrichment_bp = Blueprint(
    name="metadata_enrichment",
    api_endpoint="/sub/metadata_enrichment",
    api_version="v1",
)


@metadata_enrichment_bp.handler(is_start=True)
async def start(job_id: str, actions: ActionFactory):
    actions.go_to("dispatch_enrichment")
    return actions


@metadata_enrichment_bp.handler("dispatch_enrichment").when(
    "context.initial_data.mode == 'deep_scan'"
)
async def dispatch_enrichment_deep(actions: ActionFactory):
    actions.dispatch_task(
        task_type="analyze_file",
        skill_version="1.0.0",
        params={"target": "metadata", "deep": True},
        transitions={"success": "finished", "failure": "failed"},
    )
    return actions


@metadata_enrichment_bp.handler("dispatch_enrichment")
async def dispatch_enrichment_default(actions: ActionFactory):
    actions.dispatch_task(
        task_type="analyze_file",
        skill_version="1.0.0",
        params={"target": "metadata", "deep": False},
        transitions={"success": "finished", "failure": "failed"},
    )
    return actions


@metadata_enrichment_bp.handler("finished", is_end=True)
async def sub_finished(job_id: str):
    logger.info(f"[{job_id}] SUB-PROCESS FINISHED.")


@metadata_enrichment_bp.handler("failed", is_end=True)
async def sub_failed(job_id: str):
    logger.error(f"[{job_id}] SUB-PROCESS FAILED.")
