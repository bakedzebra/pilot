import kopf
import logging
import os

from kubernetes import config, client, watch

import service.service

config.load_kube_config()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger("pilot-pilot-controller")


@kopf.on.create('ozhaw.io', 'v1', 'pilottests')
def test_created(spec, **kwargs):
    test_name = kwargs["body"]["metadata"]["name"]
    test_namespace = kwargs["body"]["metadata"]["namespace"]

    log.info(f"The PilotTest was created with name: {test_name} in namespace: {test_namespace}.")

    service.service.update_test_phase(service.service.Phase.Created, test_name, test_namespace)

    if 'configMap' in spec["verify"]:
        for config_map in spec["verify"]['configMap']:
            config_map_namespace = test_namespace
            if 'namespace' in config_map and config_map["namespace"]:
                config_map_namespace = config_map["namespace"]

            test_config_maps(config_map["name"], config_map_namespace, spec["releaseName"])


def init_tests(namespace: str, release_name: str):
    log.info(f"Waiting HelmRelease: {release_name} to be Succeeded phase...")

    os.system('ls -l')

    v1 = client.CustomObjectsApi()
    w = watch.Watch()
    for event in w.stream(v1.list_namespaced_custom_object("helm.fluxcd.io",
                                                           "v1",
                                                           namespace,
                                                           "helmreleases")):

        print("Event: %s %s" % (event['type'], event['object'].metadata.name))

    print("Ended.")


def test_config_maps(name: str, namespace: str, release_name: str):
    print("Ended.")


if __name__ == '__main__':
    v1 = client.CustomObjectsApi()
    w = watch.Watch()
    for event in w.stream(v1.list_cluster_custom_object("helm.fluxcd.io", "v1", "helmreleases"), timeout_seconds=10):
        print("Event: %s %s" % (event['type'], event['object'].metadata.name))
    print("Finished namespace stream.")
