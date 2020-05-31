import jsonapi
from jsonapi.auth import ULFAuthentication
from jsonapi.globals import _jsonapi_global

from .constants import host


def reset_setup():
    jsonapi.setup("test_api_key", host)
    assert _jsonapi_global.auth_header == "Bearer test_api_key"
    assert _jsonapi_global.host == host


class GlobalTest(jsonapi.Resource):
    TYPE = "globaltests"


def test_class_registry():
    assert _jsonapi_global.registry['globaltests'] is GlobalTest


def test_setup_plaintext():
    jsonapi.setup("another_key", "http://some.host")
    assert _jsonapi_global.auth_header == "Bearer another_key"
    assert _jsonapi_global.host == "http://some.host"
    reset_setup()


def test_setup_ulf():
    jsonapi.setup(ULFAuthentication('public'), host)
    assert _jsonapi_global.auth_header == "ULF public"

    jsonapi.setup(ULFAuthentication('public', 'secret'), host)
    assert _jsonapi_global.auth_header == "ULF public:secret"

    reset_setup()


def test_setup_any_callable():
    jsonapi.setup(lambda: "Another key2", "http://some.host2")
    assert _jsonapi_global.auth_header == "Another key2"
    assert _jsonapi_global.host == "http://some.host2"
    reset_setup()
