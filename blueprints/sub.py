import logging
from avtomatika import Blueprint
from avtomatika.context import ActionFactory

logger = logging.getLogger("blueprints.sub")
metadata_enrichment_bp = Blueprint(
    name="metadata_enrichment", api_endpoint="/sub/metadata_enrichment"
)


# 1. Inferred state name: 'start' (from function name)
@metadata_enrichment_bp.handler(is_start=True)
async def start(job_id: str, actions: ActionFactory):
    actions.go_to("dispatch_enrichment")


# 2. Conditional routing (.when)
@metadata_enrichment_bp.handler("dispatch_enrichment").when(
    "context.initial_data.mode == 'deep_scan'"
)
async def dispatch_enrichment_deep(actions: ActionFactory):
    """Triggered only if mode == 'deep_scan' in initial_data."""
    actions.dispatch_task(
        task_type="analyze_file",
        skill_version="1.0.0",
        params={"target": "metadata", "deep": True},
        transitions={"success": "finished", "failure": "failed"},
    )


# 3. Default fallback handler (no condition)
@metadata_enrichment_bp.handler("dispatch_enrichment")
async def dispatch_enrichment_default(actions: ActionFactory):
    """Triggered if no other conditions match."""
    actions.dispatch_task(
        task_type="analyze_file",
        skill_version="1.0.0",
        params={"target": "metadata", "deep": False},
        transitions={"success": "finished", "failure": "failed"},
    )


# 4. Final transitions
@metadata_enrichment_bp.handler("finished", is_end=True)
async def sub_finished(job_id: str):
    logger.info(f"[{job_id}] SUB-PROCESS FINISHED.")


@metadata_enrichment_bp.handler("failed", is_end=True)
async def sub_failed(job_id: str):
    logger.error(f"[{job_id}] SUB-PROCESS FAILED.")
