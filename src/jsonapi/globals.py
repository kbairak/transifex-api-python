from .auth import BearerAuthentication


class _JsonApiGlobal:
    """ Our little global object. """

    def __init__(self):
        self.registry = {}  # Will map API resource types to classes

    def setup(self, auth, host=None):
        if isinstance(auth, str):
            self.auth_header = BearerAuthentication(auth)()
        else:
            self.auth_header = auth()

        if host is None:
            host = "https://rest.api.transifex.com"
        self.host = host


_jsonapi_global = _JsonApiGlobal()
setup = _jsonapi_global.setup
