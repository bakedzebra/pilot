from kubernetes import config, client

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


class PilotService(object):
    crd_config = ResourceConfig("ozhaw.io", "v1", "pilottests", "PilotHelmTest")

    def __init__(self):
        config.load_kube_config()

        self.api = client.CustomObjectsApi()