import datetime
import os

from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from test_core.service import PilotService


class KubernetesEvent(object):
    def __init__(self, log_entry: dict, namespace: str = None, component_name: str = None,
                 test_version: str = None, test_uid: str = None):
        self.namespace = namespace
        self.component_name = component_name
        self.test_version = test_version
        self.test_uid = test_uid

        self.event_name = log_entry["event_name"]
        self.message = log_entry["event_msg"]
        self.event_type = log_entry["event_type"]
        self.event_reason = log_entry["event_reason"]

        self.host = os.environ.get('NODE_NAME', os.environ.get('HOSTNAME', 'UNKNOWN'))

        self.first_timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
        self.last_timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'

    @property
    def event_body(self):
        obj_meta = client.V1ObjectMeta(generate_name="{}".format(self.event_name))
        obj_ref = client.V1ObjectReference(kind=PilotService.crd_config.kind,
                                           api_version=PilotService.crd_config.get_full_api_version(),
                                           name=self.component_name,
                                           resource_version=self.test_version,
                                           uid=self.test_uid,
                                           namespace=self.namespace)

        event_source = client.V1EventSource(component=self.component_name)

        return client.V1Event(
            involved_object=obj_ref,
            metadata=obj_meta,
            message=self.message,
            count=1,
            type=self.event_type,
            reason=self.event_reason,
            source=event_source,
            first_timestamp=self.first_timestamp,
            last_timestamp=self.last_timestamp)


if __name__ == '__main__':
    config.load_kube_config()

    v1 = client.CoreV1Api()
    log = {
        "event_name": "TestCreatedEvent",
        "event_msg": "test_core was created",
        "event_type": "Normal",
        "event_reason": "TestCreated"
    }
    try:
        obj = v1.create_namespaced_event("default", KubernetesEvent(log, "default", "default-test_core").event_body)
        print(obj)
    except ApiException as e:
        print(e)
