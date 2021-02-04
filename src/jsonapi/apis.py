from __future__ import absolute_import, unicode_literals

import requests
import six

from .auth import BearerAuthentication
from .compat import JSONDecodeError
from .exceptions import JsonApiException
from .resources import Resource


class _JsonApiMetaclass(type):
    def __new__(cls, *args, **kwargs):
        result = super(_JsonApiMetaclass, cls).__new__(cls, *args, **kwargs)

        # Use a copy, not reference to parent's registry
        result.registry = list(getattr(result, 'registry', []))

        return result


class JsonApi(six.with_metaclass(_JsonApiMetaclass, object)):
    """ Inteface for a new {json:api} API.

        - host: The URL of the API
        - auth: The authentication method. Can either be:

          1. A callable, whose return value should be a dictionary which will
             be merged with the headers of all HTTP request sent to the API
          2. A string, in which case the 'Authorization' header will be
             `Bearer <auth>`

            >>> _api = jsonapi.JsonApi(host=..., auth=...)

        The arguments are optional and can be edited later with `.setup()`

            >>> _api = jsonapi.JsonApi()
            >>> _api.setup(host=..., auth=...)

        All Resource classes that use this API should be registered to this API
        instance:

            >>> @_api.register
            ... class Foo(jsonapi.Resource):
            ...     TYPE = "foos"
    """

    HOST = None

    def __init__(self, **kwargs):
        self.type_registry = {}
        self.class_registry = {}

        for base_class in self.__class__.registry:
            # Dynamically create a subclass adding 'self' (the API connection
            # instance) as a class variable to it
            child_class = type(base_class.__name__,
                               (base_class, ),
                               {'API': self})
            self.type_registry[base_class.TYPE] = child_class
            self.class_registry[base_class.__name__] = child_class

        self.host = self.HOST
        self.headers = {}
        self.setup(**kwargs)

    def setup(self, host=None, auth=None, headers=None):
        if host is not None:
            self.host = host

        if auth is not None:
            if callable(auth):
                self.make_auth_headers = auth
            else:
                self.make_auth_headers = BearerAuthentication(auth)

        if headers is not None:
            self.headers = headers

    @classmethod
    def register(cls, klass):
        cls.registry.append(klass)
        return klass

    def __getattr__(self, attr):
        """ Access a registered API resource class. A class name or API
            resource type can be used.

                >>> class FooApi(JsonApi):
                ...     HOST = "https://api.foo.com"

                >>> @FooApi.register
                ... class Foo(Resource):
                ...     TYPE = "foos"

                >>> foo_api = FooApi()

                >>> foo_api.Foo.list()
                >>> # or
                >>> foo_api.foos.list()
        """

        try:
            return self.class_registry[attr]
        except KeyError:
            try:
                return self.type_registry[attr]
            except KeyError:
                raise AttributeError(attr)

    #                 Required args
    def request(self, method, url,
                # Not passed to requests, used to determine Content-Type
                bulk=False,
                # Forwarded to requests
                headers=None, data=None, files=None,
                allow_redirects=False,
                **kwargs):
        if url.startswith('/'):
            url = "{}{}".format(self.host, url)

        if bulk:
            content_type = 'application/vnd.api+json;profile="bulk"'
        elif (data, files) == (None, None):
            content_type = "application/vnd.api+json"
        else:
            # If data and/or files are set, requests will determine
            # Content-Type on its own
            content_type = None

        actual_headers = dict(self.headers)

        if headers is not None:
            actual_headers.update(headers)
        actual_headers.update(self.make_auth_headers())
        if content_type is not None:
            actual_headers.setdefault('Content-Type', content_type)

        response = requests.request(method, url, headers=actual_headers,
                                    data=data, files=files,
                                    allow_redirects=allow_redirects,
                                    **kwargs)

        if not response.ok:
            try:
                exc = JsonApiException(response.status_code,
                                       response.json()['errors'])
            except Exception:
                response.raise_for_status()
            else:
                raise exc
        try:
            return response.json()
        except JSONDecodeError:
            # Most likely empty response when deleting
            return response

    def new(self, data=None, type=None, **kwargs):
        """ Return a new resource instance, using the appropriate Resource
            subclass, provided that it has been registered with this API
            instance.

                >>> _api = jsonapi.JsonApi(...)
                >>> @_api.register
                ... class Foo(jsonapi.Resource):
                ...     TYPE = "foos"
                >>> obj = _api.new(type="foos", ...)

                >>> isinstance(obj, Foo)
                <<< True
        """

        if data is not None:
            if 'data' in data:
                data = data['data']
            return self.new(**data)
        else:
            if type in self.type_registry:
                klass = self.type_registry[type]
            else:
                # Lets make a new class on the fly
                class klass(Resource):
                    API = self
            return klass(**kwargs)

    def as_resource(self, data):
        """ Little convenience function when we don't know if we are dealing
            with a Resource instance or a dict describing a relationship. Will
            use the appropriate Resource subclass.
        """

        try:
            return self.new(data)
        except Exception:
            return data
