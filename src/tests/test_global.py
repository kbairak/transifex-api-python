import jsonapi
from jsonapi.auth import ULFAuthentication
from jsonapi.globals import _jsonapi_global

from .constants import host


def reset_setup():
    jsonapi.setup(host, "test_api_key")
    assert (_jsonapi_global.make_auth_headers() ==
            {'Authorization': "Bearer test_api_key"})
    assert _jsonapi_global.host == host


class GlobalTest(jsonapi.Resource):
    TYPE = "globaltests"


def test_class_registry():
    assert _jsonapi_global.registry['globaltests'] is GlobalTest


def test_setup_plaintext():
    jsonapi.setup("http://some.host", "another_key")
    assert (_jsonapi_global.make_auth_headers() ==
            {'Authorization': "Bearer another_key"})
    assert _jsonapi_global.host == "http://some.host"
    reset_setup()


def test_setup_ulf():
    jsonapi.setup(host, ULFAuthentication('public'))
    assert (_jsonapi_global.make_auth_headers() ==
            {'Authorization': "ULF public"})

    jsonapi.setup(host, ULFAuthentication('public', 'secret'))
    assert (_jsonapi_global.make_auth_headers() ==
            {'Authorization': "ULF public:secret"})

    reset_setup()


def test_setup_any_callable():
    jsonapi.setup("http://some.host2",
                  lambda: {'Authorization': "Another key2"})
    assert (_jsonapi_global.make_auth_headers() ==
            {'Authorization': "Another key2"})
    assert _jsonapi_global.host == "http://some.host2"
    reset_setup()
