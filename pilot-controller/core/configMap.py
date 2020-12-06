import logging

from kubernetes import config, client
from kubernetes.client.rest import ApiException

from service import TestResult, HelmReleaseService, PilotService, Resource

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class ConfigMapTestSuite(object):
    def __init__(self):
        self.api = client.CustomObjectsApi
        self.service = PilotService()

        self.log = logging.getLogger("ConfigMapTestSuite")
        self.log.setLevel(logging.INFO)

    def run(self, config_maps: list, namespace: str, release_name: str, test_name: str):
        for config_map in config_maps:
            cf_name = config_map["name"]
            config_map_namespace = config_map["namespace"] if 'namespace' in config_map \
                                                              and config_map["namespace"] else namespace
            for test_result in ConfigMapTest().run(config_map, config_map_namespace, release_name):
                self.service.update_result(test_result, test_name, namespace, Resource.ConfigMap, cf_name)


class ConfigMapTest(object):
    def __init__(self):
        config.load_kube_config()

        self.core_v1_api = client.CoreV1Api()
        self.log = logging.getLogger("ConfigMapTest")
        self.log.setLevel(logging.INFO)

    def run(self, config_map_config: dict, namespace: str, release_name: str):
        cf_name = config_map_config["name"]
        cf_namespace = config_map_config["namespace"] if 'namespace' in config_map_config else namespace
        try:
            test_failed = False
            config_map = self.core_v1_api.read_namespaced_config_map(cf_name, cf_namespace)

            self.log.info(f'Found ConfigMap named {cf_name}. Validating...')

            if HelmReleaseService.helm_release_annotation_name not in config_map.metadata.annotations \
                    or config_map.metadata.annotations[HelmReleaseService.helm_release_annotation_name] \
                    != HelmReleaseService.get_helm_release_annotation(namespace, release_name):
                test_failed = True
                yield TestResult(False, 'NonReleaseRelated',
                                 f'The ConfigMap {cf_name} is not controlled by release {release_name}')
            if 'data' in config_map_config and 'includes' in config_map_config['data'] \
                    and len(config_map_config['data']['includes']) != 0:
                for data_name in config_map_config['data']['includes']:
                    if data_name not in config_map.data or not config_map.data[data_name]:
                        test_failed = True
                        yield TestResult(False, 'DataValidationFailure',
                                         f'The data entry named {data_name} was not found in ConfigMap {cf_name}')
            if 'data' in config_map_config and 'count' in config_map_config['data'] \
                    and config_map_config['data']['count'] != len(config_map.data):
                test_failed = True
                yield TestResult(False, 'DataValidationFailure', f'The ConfigMap {cf_name} has {len(config_map.data)} '
                                                                 f'data entries while {config_map_config["data"]["count"]} was expected')

            if not test_failed:
                yield TestResult(True, 'TestPassed', f"The test for {cf_name} was successfully passed")
        except ApiException as e:
            self.log.error("Exception when calling CoreV1Api->read_namespaced_config_map: %s\n" % e)
            yield TestResult(True, 'ApiCallException', f"Test was unable to get and validate "
                                                       f"the ConfigMap using k8s api client")
