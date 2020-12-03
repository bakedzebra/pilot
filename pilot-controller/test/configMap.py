import asyncio
import logging

from kubernetes import config, client
from kubernetes.client.rest import ApiException

import service.service
import exception.exceptions

config.load_kube_config()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger("pilot-test-engine")
log.setLevel(logging.INFO)


# TODO: Add return of test result and message
async def test_config_maps(config_map_config: dict, namespace: str, release_name: str, request_timeout: int,
                           retries: int):
    log.info(f'Waiting HelmRelease {release_name} to be successfully deployed')
    helm_release_ready = await is_helm_release_ready(namespace, release_name, request_timeout, retries)
    if helm_release_ready:
        helm_release = get_helm_release(namespace, release_name)

        core_apiv1 = client.CoreV1Api()

        cf_name = config_map_config["name"]
        cf_namespace = config_map_config["namespace"] if 'namespace' in config_map_config else namespace
        try:
            config_map = core_apiv1.read_namespaced_config_map(cf_name, cf_namespace)

            if service.service.helm_release_annotation_name not in config_map.metadata.annotations \
                    or config_map.metadata.annotations[service.service.helm_release_annotation_name] \
                    != service.service.get_helm_release_annotation(namespace, release_name):
                # TODO: Add return of test result and message
                return False
            if 'data' in config_map_config and 'includes' in config_map_config['data'] \
                    and len(config_map_config['data']['includes']) != 0:
                for data_name in config_map_config['data']['includes']:
                    # TODO: Add return of test result and message
                    if data_name not in config_map.data or not config_map.data[data_name]:
                        return False
            if 'data' in config_map_config and 'count' in config_map_config['data'] \
                    and config_map_config['data']['count'] != len(config_map.data):
                # TODO: Add return of test result and message
                return False

            return True
        except ApiException as e:
            log.error("Exception when calling CoreV1Api->read_namespaced_config_map: %s\n" % e)
            # TODO: Add return of test result and message
            return False


async def is_helm_release_ready(namespace: str, release_name: str, request_timeout: int = 10, retries: int = None):
    try:
        helm_release = get_helm_release(namespace, release_name)

        is_ready = bool(helm_release) and helm_release['status']['phase'] in ['Succeeded', 'Deployed']

        if not is_ready and (retries is None or not retries == 1):
            print(retries)
            await asyncio.sleep(request_timeout)
            is_ready = await is_helm_release_ready(namespace, release_name,
                                                   request_timeout, None if retries is None else retries - 1)

        return (retries is None or retries > 1) and is_ready

    except ApiException as e:
        if e.status == 404:
            if retries is None or not retries == 1:
                print(retries)
                await asyncio.sleep(request_timeout)
                is_ready = await is_helm_release_ready(namespace, release_name,
                                                       request_timeout, None if retries is None else retries - 1)
                return is_ready
            else:
                return False
        else:
            log.error("Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
            raise exception.exceptions.HelmReleaseUnavailableException(namespace, release_name)


def get_helm_release(namespace: str, release_name: str):
    coapi = client.CustomObjectsApi()
    return coapi.get_namespaced_custom_object(service.service.helm_release_resource_config["group"],
                                              service.service.helm_release_resource_config["version"],
                                              namespace,
                                              service.service.helm_release_resource_config["plural"],
                                              release_name)


async def main():
    config_map = {
        "name": "success-config",
        "data": {
            "count": 3,
            "includes": ["type", "message", "success"]
        }
    }

    print(await test_config_maps(config_map, "default", "test-release", 2, 5))


if __name__ == '__main__':
    asyncio.run(main())
