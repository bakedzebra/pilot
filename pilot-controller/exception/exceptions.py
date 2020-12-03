class HelmReleaseUnavailableException(Exception):
    def __init__(self, namespace: str, release_name: str):
        self.message = f'Cannot track HelmRelease named {release_name} in namespace {namespace}. Internal K8S error.'
        super().__init__(self.message)


class ConfigMapNotFoundException(Exception):
    def __init__(self, namespace: str, name: str):
        self.message = f'Cannot find ConfigMap named {name} in namespace {namespace}.'
        super().__init__(self.message)
