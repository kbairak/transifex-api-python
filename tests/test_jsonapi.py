import responses
import transifex_api
from transifex_api.globals import _jsonapi_global
from transifex_api.jsonapi import Resource

transifex_api.setup("test_api_key")


class Foo(Resource):
    TYPE = "foos"


SIMPLE_PAYLOAD = {'type': "foos", 'id': "1", 'attributes': {'hello': "world"}}


def make_simple_assertions(foo):
    assert isinstance(foo, Foo)
    assert foo.TYPE == "foos"
    assert foo.id == "1"
    assert foo.attributes == foo.a == {'hello': "world"}
    assert foo.relationships == foo.R == {}
    assert foo.related == foo.r == {}
    assert foo.hello == "world"


def test_class_registry():
    assert _jsonapi_global.registry['foos'] is Foo


def test_setup():
    transifex_api.setup("another_key", "http://some.host")
    assert _jsonapi_global.auth_header == "Bearer another_key"
    assert _jsonapi_global.host == "http://some.host"

    transifex_api.setup("test_api_key")
    assert _jsonapi_global.auth_header == "Bearer test_api_key"
    assert _jsonapi_global.host == "https://rest.api.transifex.com"


def test_init_with_data():
    foo = Foo({'data': SIMPLE_PAYLOAD})
    make_simple_assertions(foo)
    foo = Foo(SIMPLE_PAYLOAD)
    make_simple_assertions(foo)


@responses.activate
def test_get_one():
    responses.add(responses.GET,
                  "https://rest.api.transifex.com/foos/1",
                  json={'data': SIMPLE_PAYLOAD},
                  status=200)

    foo = Foo.get('1')

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call.request.headers['Content-Type'] == "application/vnd.api+json"
    assert call.request.headers['Authorization'] == "Bearer test_api_key"

    make_simple_assertions(foo)
