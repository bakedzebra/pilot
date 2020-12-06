import functools
import logging

from kubernetes import config, client
from kubernetes.client.rest import ApiException

from service import TestResult, HelmReleaseService, PilotService, Resource
from event import KubernetesEvent, EventService, EventBody, EventReason, EventType

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class ConfigMapTestSuite(object):
    def __init__(self):
        self.api = client.CustomObjectsApi
        self.service = PilotService()
        self.events = EventService()

        self.log = logging.getLogger("ConfigMapTestSuite")
        self.log.setLevel(logging.INFO)

    def run(self, resources: list, namespace: str, release_name: str, test_name: str):
        results = []
        for config_map in resources:
            cf_name = config_map["name"]
            config_map_namespace = config_map["namespace"] if 'namespace' in config_map \
                                                              and config_map["namespace"] else namespace

            test_results = list(ConfigMapTest().run(config_map, cf_name, config_map_namespace, release_name))

            messages = map(lambda test_result: test_result.message, test_results)
            passed = functools.reduce(lambda a, b: a and b, map(lambda test_result: test_result.passed, test_results))
            results.append({
                'name': cf_name,
                'passed': passed,
                'messages': list(messages)
            })

            event = EventBody(EventReason.ConfigMapTestPassed if passed else EventReason.ConfigMapTestFailed,
                              EventType.Major, f'ConfigMap `{cf_name}` test passed successfully.' if passed else
                              f'ConfigMap `{cf_name}` test failed.')
            self.events.send(KubernetesEvent(event, namespace, test_name))

        if len(results) > 0:
            self.service.update_result(results, test_name, namespace, Resource.ConfigMap)

        return results


class ConfigMapTest(object):
    def __init__(self):
        config.load_kube_config()

        self.core_v1_api = client.CoreV1Api()
        self.log = logging.getLogger("ConfigMapTest")
        self.log.setLevel(logging.INFO)

    def run(self, resource_config: dict, name: str, namespace: str, release_name: str):
        try:
            test_failed = False
            config_map = self.core_v1_api.read_namespaced_config_map(name, namespace)

            self.log.info(f'Found ConfigMap named `{name}`. Validating...')

            if HelmReleaseService.helm_release_annotation_name not in config_map.metadata.annotations \
                    or config_map.metadata.annotations[HelmReleaseService.helm_release_annotation_name] \
                    != HelmReleaseService.get_helm_release_annotation(namespace, release_name):
                test_failed = True
                yield TestResult(False, 'NonReleaseRelated',
                                 f'The ConfigMap `{name}` is not controlled by release `{release_name}`')
            if 'data' in resource_config and 'includes' in resource_config['data'] \
                    and len(resource_config['data']['includes']) != 0:
                for data_name in resource_config['data']['includes']:
                    if data_name not in config_map.data or not config_map.data[data_name]:
                        test_failed = True
                        yield TestResult(False, 'DataValidationFailure',
                                         f'The data entry named `{data_name}` was not found in ConfigMap `{name}`')
            if 'data' in resource_config and 'count' in resource_config['data'] \
                    and resource_config['data']['count'] != len(config_map.data):
                test_failed = True
                yield TestResult(False, 'DataValidationFailure', f'The ConfigMap `{name}` has `{len(config_map.data)}` '
                                                                 f'data entries while `{resource_config["data"]["count"]}` was expected')

            if not test_failed:
                yield TestResult(True, 'TestPassed', f"The test for `{name}` was successfully passed")
        except ApiException as e:
            self.log.error("Exception when calling CoreV1Api->read_namespaced_config_map: %s\n" % e)
            yield TestResult(False, 'ApiCallException', f"Test was unable to get and validate "
                                                        f"the ConfigMap using k8s api client")
