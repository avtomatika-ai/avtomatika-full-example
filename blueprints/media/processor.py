from avtomatika import Blueprint, ActionFactory

# No api_endpoint specified - should be generated as /media/processor/media_cleanup
blueprint = Blueprint(name="media_cleanup")


@blueprint.handler("start", is_start=True)
async def start(job_id: str, data: dict, actions: ActionFactory):
    print(f"Cleaning up media for job {job_id}")
    await actions.go_to("finished")


@blueprint.handler("finished", is_end=True)
async def finished(job_id: str):
    print(f"Media cleanup finished for job {job_id}")
