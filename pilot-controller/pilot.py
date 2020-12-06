import asyncio

import kopf
import logging

from kubernetes import config
from concurrent.futures import ThreadPoolExecutor

from service import PilotService, Phase, Resource
from core import ConfigMapTestSuite

config.load_kube_config()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger("pilot-controller")

HELM_PHASES = {}
executor = ThreadPoolExecutor()

lock = asyncio.Lock()


@kopf.on.event('helm.fluxcd.io', 'v1', 'helmreleases')
async def on_helm_event(event, **_):
    if 'status' in event["object"] and 'phase' in event["object"]["status"] and \
            is_release_ready(event["object"]["status"]["phase"]):
        async with lock:
            HELM_PHASES[event["object"]["metadata"]["name"]] = {
                "namespace": event["object"]["metadata"]["namespace"],
                "ready": True
            }


@kopf.on.create('ozhaw.io', 'v1', 'pilottests')
async def test_created(spec, **kwargs):
    test_name = kwargs["body"]["metadata"]["name"]
    test_namespace = kwargs["body"]["metadata"]["namespace"]
    release_name = spec["releaseName"]

    timeout = spec["timeout"] if "timeout" in spec else 10
    retries = spec["retries"] if "retries" in spec else None

    service = PilotService()

    log.info(f"The PilotTest was created with name: {test_name} in namespace: {test_namespace}.")

    service.update_test_phase(Phase.Created, test_name, test_namespace)

    helm_release_found = False
    while retries is None or retries > 0:
        async with lock:
            if release_name in HELM_PHASES \
                    and HELM_PHASES[release_name]["namespace"] == kwargs["body"]["metadata"]["namespace"] \
                    and HELM_PHASES[release_name]["ready"]:
                log.info(f"Found release: {release_name} and starting tests!")
                helm_release_found = True
                break
        log.info("Waiting for helm release...")
        retries = retries - 1 if retries is not None else None
        await asyncio.sleep(timeout)

    if helm_release_found:
        future = executor.submit(run_test, spec, test_namespace, release_name, test_name, service)
    else:
        log.info(f"Cannot find release: {release_name} for specified timeout. Failing the test")


def is_release_ready(phase: str = None):
    return phase == 'Succeeded' or phase == 'Deployed'


def run_test(spec: dict, namespace: str, release_name: str, test_name: str, service: PilotService):
    service.initiate_results(test_name, namespace)
    if Resource.ConfigMap in spec["verify"]:
        ConfigMapTestSuite().run(spec["verify"][Resource.ConfigMap], namespace, release_name, test_name)
