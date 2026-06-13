import logging
from typing import Any
from avtomatika import Blueprint
from avtomatika.context import ActionFactory

logger = logging.getLogger("blueprints.main")

main_bp = Blueprint(
    name="full_showcase", api_endpoint="/submit/full_showcase", api_version="v1"
)


@main_bp.handler(is_start=True)
async def start(
    job_id: str,
    initial_data: dict[str, Any],
    actions: ActionFactory,
):
    actions.send_event(
        "pipeline_initialized", {"version": "1.0b26", "user_tier": "vip"}
    )

    actions.await_human_approval(
        integration="admin_console",
        message="Please approve this expensive transcoding job.",
        transitions={"approved": "dispatch_transcoding", "rejected": "failed"},
    )
    return actions


@main_bp.handler
async def dispatch_transcoding(job_id: str, actions: ActionFactory):
    actions.dispatch_task(
        task_type="transcode_video",
        skill_version="1.0.0",
        params={},
        resource_requirements={
            "properties": {"cpu_cores": 2, "ram_gb": 4},
            "installed_artifacts": [{"name": "video-preset-v1"}],
        },
        max_cost=0.005,
        dispatch_timeout_seconds=60,
        result_timeout_seconds=300,
        transitions={"success": "fan_out_analysis", "failure": "failed"},
    )
    return actions


@main_bp.handler
async def fan_out_analysis(job_id: str, actions: ActionFactory):
    actions.send_event("analysis_started", {"count": 1})

    task_list = [
        {
            "type": "analyze_file",
            "skill_version": "1.0.0",
            "params": {"resource_id": "video"},
            "transitions": {"success": "finished", "failure": "failed"},
        }
    ]
    actions.dispatch_parallel(tasks=task_list, aggregate_into="aggregate_results")
    return actions


@main_bp.aggregator
async def aggregate_results(aggregation_results: dict, actions: ActionFactory):
    logger.info(f"AGGREGATOR: Merging {len(aggregation_results)} results.")
    actions.update_context(
        {"is_aggregated": True, "analysis_summary": aggregation_results}
    )
    actions.go_to("enrich_metadata")
    return actions


@main_bp.handler
async def enrich_metadata(job_id: str, actions: ActionFactory):
    actions.run_blueprint(
        blueprint_name="metadata_enrichment",
        initial_data={"target": "video_metadata", "mode": "deep_scan"},
        transitions={"success": "generate_report", "failure": "failed"},
    )
    return actions


@main_bp.handler
async def generate_report(job_id: str, actions: ActionFactory):
    actions.dispatch_task(
        task_type="generate_video_report",
        skill_version="1.0.0",
        params={},
        transitions={"success": "cleanup_media", "failure": "failed"},
    )
    return actions


@main_bp.handler
async def cleanup_media(job_id: str, actions: ActionFactory):
    actions.run_blueprint(
        blueprint_name="media_cleanup",
        initial_data={"job_id": job_id},
        transitions={"success": "finished", "failure": "failed"},
    )
    return actions


@main_bp.handler(is_end=True)
async def finished(job_id: str):
    logger.info(f"[{job_id}] MAIN PROCESS FINISHED.")


@main_bp.handler(is_end=True)
async def failed(job_id: str):
    logger.info(f"[{job_id}] MAIN PROCESS FAILED.")
