import logging

from kubernetes import config, client
from kubernetes.client.rest import ApiException

import test_core.service

config.load_kube_config()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger("pilot-test_core-engine")
log.setLevel(logging.INFO)


# TODO: Add return of test_core result and message
async def test_config_maps(config_map_config: dict, namespace: str, release_name: str):
    core_apiv1 = client.CoreV1Api()

    cf_name = config_map_config["name"]
    cf_namespace = config_map_config["namespace"] if 'namespace' in config_map_config else namespace
    try:
        config_map = core_apiv1.read_namespaced_config_map(cf_name, cf_namespace)

        if test_core.service.helm_release_annotation_name not in config_map.metadata.annotations \
                or config_map.metadata.annotations[test_core.service.helm_release_annotation_name] \
                != test_core.service.get_helm_release_annotation(namespace, release_name):
            # TODO: Add return of test_core result and message
            return False
        if 'data' in config_map_config and 'includes' in config_map_config['data'] \
                and len(config_map_config['data']['includes']) != 0:
            for data_name in config_map_config['data']['includes']:
                # TODO: Add return of test_core result and message
                if data_name not in config_map.data or not config_map.data[data_name]:
                    return False
        if 'data' in config_map_config and 'count' in config_map_config['data'] \
                and config_map_config['data']['count'] != len(config_map.data):
            # TODO: Add return of test_core result and message
            return False

        return True
    except ApiException as e:
        log.error("Exception when calling CoreV1Api->read_namespaced_config_map: %s\n" % e)
        # TODO: Add return of test_core result and message
        return False


def get_helm_release(namespace: str, release_name: str):
    custom_object_api = client.CustomObjectsApi()
    return custom_object_api.get_namespaced_custom_object(test_core.service.helm_release_resource_config["group"],
                                                          test_core.service.helm_release_resource_config["version"],
                                                          namespace,
                                                          test_core.service.helm_release_resource_config["plural"],
                                                          release_name)
