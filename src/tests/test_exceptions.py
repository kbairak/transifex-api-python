import jsonapi
import responses
from jsonapi.exceptions import JsonApiException

from .constants import host

_api = jsonapi.JsonApi(host=host, auth="test_api_key")


@_api.register
class Foo(jsonapi.Resource):
    TYPE = "foos"


@responses.activate
def test_exception_during_create():
    responses.add(
        responses.POST,
        f"{host}/foos",
        json={'errors': [{
            'status': "409",
            'code': "conflict",
            'title': "Conflict error",
            'detail': "username 'Foo' is already taken",
            'source': {'pointer': "/data/attributes/username"},
        }]},
        status=409,
    )

    exc = None
    try:
        Foo.create(attributes={'username': "Foo"})
    except JsonApiException as e:
        exc = e

    assert exc.status == "409"
    assert exc.code == "conflict"
    assert exc.title == "Conflict error"
    assert exc.detail == "username 'Foo' is already taken"
    assert exc.source == {'pointer': "/data/attributes/username"}

    assert exc.errors[0].status == "409"
    assert exc.errors[0].code == "conflict"
    assert exc.errors[0].title == "Conflict error"
    assert exc.errors[0].detail == "username 'Foo' is already taken"
    assert exc.errors[0].source == {'pointer': "/data/attributes/username"}
