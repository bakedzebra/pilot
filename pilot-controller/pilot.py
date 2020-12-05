import asyncio

import kopf
import logging

from kubernetes import config
from concurrent.futures import ThreadPoolExecutor

config.load_kube_config()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger("pilot-pilot-controller")

HELM_PHASES = {}
executor = ThreadPoolExecutor()

lock = asyncio.Lock()


@kopf.on.event('helm.fluxcd.io', 'v1', 'helmreleases')
async def on_helm_event(event, **_):
    if is_release_ready(event["object"]["status"]["phase"]):
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

    log.info(f"The PilotTest was created with name: {test_name} in namespace: {test_namespace}.")

    test_core.service.update_test_phase(test_core.service.Phase.Created, test_name, test_namespace)

    while retries is None or retries > 0:
        helm_release_found = False
        async with lock:
            if release_name in HELM_PHASES \
                    and HELM_PHASES[release_name]["namespace"] == kwargs["body"]["metadata"]["namespace"] \
                    and HELM_PHASES[release_name]["ready"]:

                print(f"Found release: {release_name} and starting tests!")
                helm_release_found = True
                break
        print("Waiting for helm release...")
        retries = retries - 1 if retries is not None else None
        await asyncio.sleep(timeout)

    if helm_release_found:
        executor.submit(run_test, spec)
    else:
        print(f"Cannot find release: {release_name} for specified timeout. Failing the test")


def is_release_ready(phase: str = None):
    return phase == 'Succeeded' or phase == 'Deployed'


def run_test(spec: dict):
    print(f"Starting test {spec['releaseName']}")

# def test_created1(spec, **kwargs):
#
#     if 'configMap' in spec["verify"]:
#         for config_map in spec["verify"]['configMap']:
#             config_map_namespace = test_namespace
#             if 'namespace' in config_map and config_map["namespace"]:
#                 config_map_namespace = config_map["namespace"]
#
#             test_config_maps(config_map["name"], config_map_namespace, spec["releaseName"])
