import enum
import logging

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from datetime import datetime


config.load_kube_config()

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
log = logging.getLogger("pilot-service")

pts_resource_config = {
    "group": "ozhaw.io",
    "version": "v1",
    "plural": "pilottests"
}

helm_release_resource_config = {
    "group": "helm.fluxcd.io",
    "version": "v1",
    "plural": "helmreleases"
}

helm_release_annotation_name = "helm.fluxcd.io/antecedent"


def get_helm_release_annotation(namespace: str, release_name: str):
    return f'{namespace}:helmrelease/{release_name}'


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


def update_test_phase(phase: Phase, name: str, namespace: str):
    log.info(f"Updating test phase into: {phase.get_phase_name} for test: {name}")

    custom_objects_sapi = client.CustomObjectsApi()

    try:
        pts_status_patch = get_status_phase(phase)

        pts = custom_objects_sapi.patch_namespaced_custom_object_status(
            namespace=namespace,
            name=name,
            body=pts_status_patch,
            group=pts_resource_config["group"],
            version=pts_resource_config["version"],
            plural=pts_resource_config["plural"]
        )

        log.info(f'PilotTest {name} was updated with following status: {pts["status"]["phase"]}')
    except ApiException as e:
        log.error("Exception when calling CustomObjectsApi->patch_namespaced_custom_object_status: %s\n" % e)


def add_test_condition(condition: Condition, name: str, namespace: str, message: str, reason: str, status: bool):
    log.info(f"Adding new status condition: {condition.get_condition_name} for test: {name}")

    custom_objects_sapi = client.CustomObjectsApi()

    try:
        pts_condition_patch = get_condition(condition, message, reason, status)

        pts = custom_objects_sapi.patch_namespaced_custom_object_status(
            namespace=namespace,
            name=name,
            body=pts_condition_patch,
            group=pts_resource_config["group"],
            version=pts_resource_config["version"],
            plural=pts_resource_config["plural"]
        )

        log.info(f'PilotTest {name} was updated with following condition: {pts["status"]["conditions"]}')
    except ApiException as e:
        log.error("Exception when calling CustomObjectsApi->patch_namespaced_custom_object_status: %s\n" % e)


if __name__ == '__main__':
    print(f'Phase: {get_status_phase(Phase.Passed)}')
    print(f'Condition: {get_condition(Condition.Passed, "All tests were passed", "AllTestsPassed", True)}')
