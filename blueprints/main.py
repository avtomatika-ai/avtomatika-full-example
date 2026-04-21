import logging
from typing import Any
from avtomatika import Blueprint
from avtomatika.context import ActionFactory

logger = logging.getLogger("blueprints.main")

# State names are automatically inferred from function names.
main_bp = Blueprint(name="full_showcase", api_endpoint="/submit/full_showcase")


@main_bp.handler(is_start=True)
async def start(
    job_id: str,
    initial_data: dict[str, Any],
    actions: ActionFactory,
):
    """The entry point of the pipeline."""
    # Custom business event emission
    actions.send_event(
        "pipeline_initialized", {"version": "1.0b21", "user_tier": "vip"}
    )

    # 1. Advanced Feature: Human-in-the-Loop
    # The pipeline will pause here until external approval via API
    actions.await_human_approval(
        integration="admin_console",
        message="Please approve this expensive transcoding job.",
        transitions={"approved": "dispatch_transcoding", "rejected": "failed"},
    )


@main_bp.handler
async def dispatch_transcoding(job_id: str, actions: ActionFactory):
    """Dispatches the main heavy task with resource constraints."""
    # 2. Advanced Feature: Task Constraints (Resources, Max Cost & Timeouts)
    # 3. Advanced Feature: Resource Hints (Targeting specific hardware/cache)
    actions.dispatch_task(
        task_type="transcode_video",
        skill_version="1.0.0",
        params={},
        resource_requirements={"properties": {"cpu_cores": 2, "ram_gb": 4}},
        resource_hint="video-preset-v1",  # Target workers with hot cache
        max_cost=0.005,
        dispatch_timeout_seconds=60,
        result_timeout_seconds=300,
        transitions={"success": "fan_out_analysis", "failure": "failed"},
    )


@main_bp.handler
async def fan_out_analysis(job_id: str, actions: ActionFactory):
    """Demonstrates parallel execution (Fan-out)."""
    # Emit event before parallel execution
    actions.send_event("analysis_started", {"count": 1})

    tasks = [
        {
            "type": "analyze_file",
            "skill_version": "1.0.0",
            "params": {"resource_id": "video"},
            "transitions": {"success": "finished", "failure": "failed"},
        }
    ]
    actions.dispatch_parallel(tasks=tasks, aggregate_into="aggregate_results")


@main_bp.aggregator
async def aggregate_results(aggregation_results: dict, actions: ActionFactory):
    """Demonstrates results aggregation (Fan-in)."""
    # aggregation_results contains {task_id: result_obj}
    actions.update_context(
        {"is_aggregated": True, "analysis_summary": aggregation_results}
    )
    actions.go_to("enrich_metadata")


@main_bp.handler
async def enrich_metadata(job_id: str, actions: ActionFactory):
    """Demonstrates Hierarchical Logic (Running a Sub-Blueprint)."""
    # 4. Hierarchical Logic: Run Sub-Blueprint
    # We pass 'mode' to trigger conditional routing in the sub-blueprint
    actions.run_blueprint(
        blueprint_name="metadata_enrichment",
        initial_data={"target": "video_metadata", "mode": "deep_scan"},
        transitions={"success": "generate_report", "failure": "failed"},
    )


@main_bp.handler
async def generate_report(job_id: str, actions: ActionFactory):
    """Final task before finishing the job."""
    actions.dispatch_task(
        task_type="generate_video_report",
        skill_version="1.0.0",
        params={},
        transitions={"success": "finished", "failure": "failed"},
    )


@main_bp.handler(is_end=True)
async def finished(job_id: str):
    """Final success state."""
    logger.info(f"[{job_id}] MAIN PROCESS FINISHED.")


@main_bp.handler(is_end=True)
async def failed(job_id: str):
    """Final failure state."""
    logger.info(f"[{job_id}] MAIN PROCESS FAILED.")
