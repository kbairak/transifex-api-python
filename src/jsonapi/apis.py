import json

import requests

from .auth import BearerAuthentication
from .exceptions import JsonApiException


class JsonApi:
    def __init__(self, host=None, auth=None):
        self.registry = {}
        self.setup(host, auth)

    def setup(self, host=None, auth=None):
        if host is not None:
            self.host = host

        if auth is not None:
            if callable(auth):
                self.make_auth_headers = auth
            else:
                self.make_auth_headers = BearerAuthentication(auth)

    def register(self, klass):
        if klass.TYPE is not None:
            self.registry[klass.TYPE] = klass
        klass.API = self
        return klass

    #                 Required args
    def request(self, method, url, *,
                # Not passed to requests, used to determine Content-Type
                bulk=False,
                # Forwarded to requests
                headers=None, data=None, files=None,
                allow_redirects=False,
                **kwargs):
        if url.startswith('/'):
            url = f"{self.host}{url}"

        if bulk:
            content_type = 'application/vnd.api+json;profile="bulk"'
        elif (data, files) == (None, None):
            content_type = "application/vnd.api+json"
        else:
            # If data and/or files are set, requests will determine
            # Content-Type on its own
            content_type = None

        if headers is None:
            headers = {}
        headers.update(self.make_auth_headers())
        if content_type is not None:
            headers.setdefault('Content-Type', content_type)

        response = requests.request(method, url, headers=headers,
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
        except json.JSONDecodeError:
            # Most likely empty response when deleting
            return response

    def new(self, data=None, *, type=None, **kwargs):
        if data is not None:
            if 'data' in data:
                data = data['data']
            return self.new(**data)
        else:
            klass = self.registry[type]
            return klass(**kwargs)

    def as_resource(self, data):
        try:
            return self.new(data)
        except Exception:
            return data

    def get(self, id, type, include=None):
        instance = self.new(type=type, id=id)
        instance.reload(include=include)
        return instance

    def create(self, *args, **kwargs):
        instance = self.new(*args, **kwargs)
        if instance.id is not None:
            raise ValueError("'id' supplied as part of a new instance")
        instance.save()
        return instance
