import enum
import logging
from datetime import datetime

from kubernetes import config, client
from kubernetes.client.rest import ApiException

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class ResourceConfig(object):
    def __init__(self, group: str = None, version: str = None, plural: str = None, kind: str = None):
        self.__group = group
        self.__version = version
        self.__plural = plural
        self.__kind = kind

    @property
    def group(self):
        return self.__group

    @property
    def version(self):
        return self.__version

    @property
    def plural(self):
        return self.__plural

    @property
    def kind(self):
        return self.__kind

    @classmethod
    def get_full_api_version(cls):
        return f'{cls.group}/{cls.version}'


class Phase(enum.Enum):
    Created = 1
    Running = 2
    Passed = 3
    Failed = 4
    ApplicationError = 5

    @property
    def get_phase_name(self):
        return self.name


class Condition(enum.Enum):
    Passed = 1
    Failed = 2
    Exported = 3

    @property
    def get_condition_name(self):
        return self.name


def get_status_phase(phase: Phase):
    return {
        'status': {
            'phase': phase.get_phase_name
        }
    }


def get_condition(condition_name: Condition, message: str, reason: str, status: bool):
    return {
        'status': {
            'conditions': [
                {
                    "type": condition_name.get_condition_name,
                    "last_probe_time": datetime.now(),
                    "last_transition_time": datetime.now(),
                    "message": message,
                    "reason": reason,
                    "status": ("False", "True")[status]
                }
            ]
        }
    }


class PilotService(object):
    crd_config = ResourceConfig("ozhaw.io", "v1", "pilottests", "PilotHelmTest")

    def __init__(self):
        config.load_kube_config()

        self.api = client.CustomObjectsApi()

        self.log = logging.getLogger("PilotService")
        self.log.setLevel(logging.INFO)

    def update_test_phase(self, phase: Phase, name: str, namespace: str):
        self.log.info(f"Updating test phase into: {phase.get_phase_name} for test: {name}")

        try:
            pts_status_patch = get_status_phase(phase)

            pts = self.api.patch_namespaced_custom_object_status(
                namespace=namespace,
                name=name,
                body=pts_status_patch,
                group=self.crd_config.group,
                version=self.crd_config.version,
                plural=self.crd_config.plural
            )

            self.log.info(f'PilotTest {name} was updated with following status: {pts["status"]["phase"]}')
        except ApiException as e:
            self.log.error("Exception when calling CustomObjectsApi->patch_namespaced_custom_object_status: %s\n" % e)

    def add_test_condition(self, condition: Condition, name: str, namespace: str, message: str, reason: str,
                           status: bool):
        self.log.info(f"Adding new status condition: {condition.get_condition_name} for test: {name}")

        try:
            pts_condition_patch = get_condition(condition, message, reason, status)

            pts = self.api.patch_namespaced_custom_object_status(
                namespace=namespace,
                name=name,
                body=pts_condition_patch,
                group=self.crd_config.group,
                version=self.crd_config.version,
                plural=self.crd_config.plural
            )

            self.log.info(f'PilotTest {name} was updated with following condition: {pts["status"]["conditions"]}')
        except ApiException as e:
            self.log.error("Exception when calling CustomObjectsApi->patch_namespaced_custom_object_status: %s\n" % e)
