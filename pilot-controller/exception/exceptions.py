class ResourceNotFoundException(Exception):
    def __init__(self, namespace: str, name: str, resource: str):
        self.message = f'Cannot find `{resource}` named `{name}` in namespace `{namespace}`.'
        super().__init__(self.message)