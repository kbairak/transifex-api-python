import transifex_api
from transifex_api.globals import _jsonapi_global
from transifex_api.jsonapi import Resource
from transifex_api.auth import ULFAuthentication

from .constants import host


def reset_setup():
    transifex_api.setup("test_api_key")
    assert _jsonapi_global.auth_header == "Bearer test_api_key"
    assert _jsonapi_global.host == host


class GlobalTest(Resource):
    TYPE = "globaltests"


def test_class_registry():
    assert _jsonapi_global.registry['globaltests'] is GlobalTest


def test_setup_plaintext():
    transifex_api.setup("another_key", "http://some.host")
    assert _jsonapi_global.auth_header == "Bearer another_key"
    assert _jsonapi_global.host == "http://some.host"
    reset_setup()


def test_setup_ulf():
    transifex_api.setup(ULFAuthentication('public'))
    assert _jsonapi_global.auth_header == "ULF public"

    transifex_api.setup(ULFAuthentication('public', 'secret'))
    assert _jsonapi_global.auth_header == "ULF public:secret"

    reset_setup()


def test_setup_any_callable():
    transifex_api.setup(lambda: "Another key2", "http://some.host2")
    assert _jsonapi_global.auth_header == "Another key2"
    assert _jsonapi_global.host == "http://some.host2"
    reset_setup()
