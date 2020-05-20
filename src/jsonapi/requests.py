import json

import requests

from .exceptions import JsonApiException
from .globals import _jsonapi_global


#                    Required args
def _jsonapi_request(method, url, *,
                     # Not passed to requests, used to determine Content-Type
                     bulk=False,
                     # Forwarded to requests
                     headers=None, data=None, files=None,
                     allow_redirects=False,
                     **kwargs):

    if url.startswith('/'):
        url = f"{_jsonapi_global.host}{url}"

    if bulk:
        content_type = 'application/vnd.api+json;profile="bulk"'
    elif (data, files) == (None, None):
        content_type = "application/vnd.api+json"
    else:
        # If data and/or files are set, requests will determine Content-Type on
        # its own
        content_type = None

    if headers is None:
        headers = {}
    headers.setdefault('Authorization', _jsonapi_global.auth_header)
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
