import json

import requests

from .exceptions import JsonApiException
from .globals import _jsonapi_global


def _jsonapi_request(method, url, *,
                     headers=None, bulk=False, allow_redirects=False,
                     files=None,
                     **kwargs):
    if url.startswith('/'):
        url = f"{_jsonapi_global.host}{url}"

    if headers is None:
        headers = {}
    headers['Authorization'] = _jsonapi_global.auth_header
    if bulk:
        headers['Content-Type'] = 'application/vnd.api+json;profile="bulk"'
    elif files is None:
        headers['Content-Type'] = "application/vnd.api+json"

    response = requests.request(method, url, headers=headers,
                                allow_redirects=allow_redirects, files=files,
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