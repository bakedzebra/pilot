import logging

from kubernetes import config, client

from service import ResourceConfig

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class HelmReleaseService(object):
    crd_config = ResourceConfig("helm.fluxcd.io", "v1", "helmreleases", "HelmRelease")
    helm_release_annotation_name = "helm.fluxcd.io/antecedent"

    @staticmethod
    def get_helm_release_annotation(namespace: str, release_name: str):
        return f'{namespace}:helmrelease/{release_name}'

    def __init__(self):
        config.load_kube_config()

        self.api = client.CustomObjectsApi()

        self.log = logging.getLogger("HelmReleaseService")
        self.log.setLevel(logging.INFO)

    def get_helm_release(self, namespace: str, release_name: str):
        custom_object_api = client.CustomObjectsApi()
        return custom_object_api.get_namespaced_custom_object(self.crd_config.group,
                                                              self.crd_config.version,
                                                              namespace,
                                                              self.crd_config.plural,
                                                              release_name)
