from .auth import BearerAuthentication


class _JsonApiGlobal:
    """ Our little global object. """

    def __init__(self):
        self.registry = {}  # Will map API resource types to classes

    def setup(self, host, auth):
        if callable(auth):
            self.make_auth_headers = auth
        else:
            self.make_auth_headers = BearerAuthentication(auth)

        self.host = host


_jsonapi_global = _JsonApiGlobal()
setup = _jsonapi_global.setup
