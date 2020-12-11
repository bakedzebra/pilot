import datetime
import enum
import logging
import os

from datetime import datetime
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from service import PilotService

logging.basicConfig(format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


class EventType(enum.Enum):
    Normal = 1
    Major = 2
    Critical = 3


class EventReason(str, enum.Enum):
    ReleaseNotFound = 'Test_not_found'

    TestCreated = 'Test_created_event'

    ConfigMapTestStarted = 'ConfigMap_test_started'
    ConfigMapTestFinished = 'ConfigMap_test_finished'
    ConfigMapTestPassed = 'ConfigMap_test_passed'
    ConfigMapTestFailed = 'ConfigMap_test_failed'


class EventBody(object):
    def __init__(self, reason: EventReason, event_type: EventType, message: str):
        self.reason = reason
        self.event_type = event_type
        self.message = message


class KubernetesEvent(object):
    def __init__(self, event_body: EventBody, namespace: str = None, component_name: str = None):
        self.namespace = namespace
        self.component_name = component_name
        self.__event_body = event_body

        self.host = os.environ.get('NODE_NAME', os.environ.get('HOSTNAME', 'UNKNOWN'))

        self.first_timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'
        self.last_timestamp = datetime.utcnow().isoformat()[:-3] + 'Z'

        self.service = PilotService()

    @property
    def event_body(self):
        test = self.service.get_test(self.component_name, self.namespace)

        obj_meta = client.V1ObjectMeta(generate_name="{}".format(self.__event_body.reason.value))
        obj_ref = client.V1ObjectReference(kind=PilotService.test_crd_config.kind,
                                           api_version=PilotService.test_crd_config.get_full_api_version(),
                                           name=self.component_name,
                                           resource_version=test['metadata']['resourceVersion'],
                                           uid=test['metadata']['uid'],
                                           namespace=self.namespace)

        event_source = client.V1EventSource(component=self.component_name)

        return client.V1Event(
            involved_object=obj_ref,
            metadata=obj_meta,
            message=self.__event_body.message,
            count=1,
            type=self.__event_body.event_type.name,
            reason=self.__event_body.reason.name,
            source=event_source,
            first_timestamp=self.first_timestamp,
            last_timestamp=self.last_timestamp)


class EventService(object):
    def __init__(self):
        config.load_kube_config()

        self.api = client.CoreV1Api()

        self.log = logging.getLogger("EventService")
        self.log.setLevel(logging.INFO)

    def send(self, event: KubernetesEvent):
        try:
            self.api.create_namespaced_event(event.namespace, event.event_body)
        except ApiException as e:
            self.log.error("Exception when calling CoreV1Api->create_namespaced_event: %s\n" % e)
