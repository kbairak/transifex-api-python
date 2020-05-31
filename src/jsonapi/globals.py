from .auth import BearerAuthentication


class _JsonApiGlobal:
    """ Our little global object. """

    def __init__(self):
        self.registry = {}  # Will map API resource types to classes

    def setup(self, auth, host):
        if isinstance(auth, str):
            self.auth_header = BearerAuthentication(auth)()
        else:
            self.auth_header = auth()

        self.host = host


_jsonapi_global = _JsonApiGlobal()
setup = _jsonapi_global.setup
