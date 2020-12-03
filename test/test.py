import asyncio

import kopf

TASKS = {}


@kopf.on.event('helm.fluxcd.io', 'v1', 'helmreleases')
async def on_helm_event(event, **_):
    TASKS[event["object"]["metadata"]["name"]] = {
        "namespace": event["object"]["metadata"]["namespace"],
        "task": asyncio.create_task(is_release_ready(event["object"]["status"]["phase"]))
    }


@kopf.on.create('ozhaw.io', 'v1', 'pilottests')
async def test_created(spec, **kwargs):
    release_name = spec["releaseName"]
    while release_name not in TASKS or TASKS[release_name]["namespace"] != kwargs["body"]["metadata"]["namespace"] \
            or not (await TASKS[release_name]["task"]):
        print("Waiting for helm release...")
        await asyncio.sleep(1)
    print("Found release and starting tests!")


async def is_release_ready(phase: str = None):
    return phase == 'Succeeded' or phase == 'Deployed'
