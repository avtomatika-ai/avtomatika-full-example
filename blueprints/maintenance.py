import logging
from typing import Any
from avtomatika import Blueprint
from avtomatika.context import ActionFactory

logger = logging.getLogger("blueprints.maintenance")
maintenance_bp = Blueprint(
    name="periodic_maintenance", api_endpoint="/maintenance/run", api_version="v1"
)


@maintenance_bp.handler("start", is_start=True)
async def maintenance_start(
    job_id: str, initial_data: dict[str, Any], actions: ActionFactory
):
    actions.go_to("run_cleanup")
    return actions


@maintenance_bp.handler("run_cleanup")
async def run_cleanup(job_id: str, actions: ActionFactory):
    actions.dispatch_task(
        task_type="analyze_file",
        skill_version="1.0.0",
        params={"target": "/tmp", "action": "purge"},
        transitions={"success": "finished", "failure": "failed"},
    )
    return actions


@maintenance_bp.handler("finished", is_end=True)
async def maintenance_finished(job_id: str):
    logger.info(f"[{job_id}] MAINTENANCE FINISHED.")


@maintenance_bp.handler("failed", is_end=True)
async def maintenance_failed(job_id: str):
    logger.error(f"[{job_id}] MAINTENANCE FAILED.")
