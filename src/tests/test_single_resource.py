import json
from copy import deepcopy

import responses
import jsonapi

from .constants import host

jsonapi.setup("test_api_key")


class Foo(jsonapi.Resource):
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


def test_init():
    foo = Foo(id="1", attributes={'hello': "world"})
    make_simple_assertions(foo)
    foo = Foo({'data': SIMPLE_PAYLOAD})
    make_simple_assertions(foo)
    foo = Foo(SIMPLE_PAYLOAD)
    make_simple_assertions(foo)


def test_new():
    foo = jsonapi.Resource.new(type="foos", id="1",
                               attributes={'hello': "world"})
    make_simple_assertions(foo)
    foo = jsonapi.Resource.new({'data': SIMPLE_PAYLOAD})
    make_simple_assertions(foo)
    foo = jsonapi.Resource.new(SIMPLE_PAYLOAD)
    make_simple_assertions(foo)


def test_as_resource():
    foo = Foo(SIMPLE_PAYLOAD)
    assert (jsonapi.Resource.as_resource(foo).as_resource_identifier() ==
            {'type': "foos", 'id': "1"})
    assert (jsonapi.Resource.as_resource({'data': SIMPLE_PAYLOAD}).
            as_resource_identifier() == {'type': "foos", 'id': "1"})
    assert (jsonapi.Resource.
            as_resource(SIMPLE_PAYLOAD).
            as_resource_identifier() ==
            {'type': "foos", 'id': "1"})


def test_setattr():
    foo = Foo(SIMPLE_PAYLOAD)
    foo.hello = "WORLD"
    assert foo.hello == "WORLD"
    assert foo.a == foo.attributes == {'hello': "WORLD"}


@responses.activate
def test_reload():
    foo = Foo(SIMPLE_PAYLOAD)

    new_payload = deepcopy(SIMPLE_PAYLOAD)
    new_payload['attributes']['hello'] = "WORLD"
    responses.add(responses.GET, f"{host}/foos/1", json={'data': new_payload})

    foo.reload()
    assert foo.hello == "WORLD"
    assert foo.a == foo.attributes == {'hello': "WORLD"}


@responses.activate
def test_get_one():
    responses.add(responses.GET, f"{host}/foos/1",
                  json={'data': SIMPLE_PAYLOAD})

    foo = Foo.get('1')

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert call.request.headers['Content-Type'] == "application/vnd.api+json"
    assert call.request.headers['Authorization'] == "Bearer test_api_key"

    make_simple_assertions(foo)

    foo = jsonapi.Resource.get('1', type="foos")

    assert len(responses.calls) == 2
    call = responses.calls[0]
    assert call.request.headers['Content-Type'] == "application/vnd.api+json"
    assert call.request.headers['Authorization'] == "Bearer test_api_key"

    make_simple_assertions(foo)


@responses.activate
def test_save_existing():
    foo = Foo(SIMPLE_PAYLOAD)

    new_payload = deepcopy(SIMPLE_PAYLOAD)
    new_payload['attributes']['hello'] = "WORLD"
    responses.add(responses.PATCH, f"{host}/foos/1",
                  json={'data': new_payload})

    foo.hello = "WORLD"
    foo.save()

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert (call.request.body.decode('utf8') ==
            json.dumps({'data': new_payload}))


@responses.activate
def test_save_new():
    new_payload = deepcopy(SIMPLE_PAYLOAD)
    new_payload['attributes']['created'] = "NOW!!!"
    responses.add(responses.POST, f"{host}/foos", json={'data': new_payload})

    foo = Foo(attributes={'hello': "world"})
    foo.save()

    assert foo.id == "1"
    assert foo.created == "NOW!!!"
    assert foo.a == foo.attributes == {'hello': "world", 'created': "NOW!!!"}


@responses.activate
def test_create():
    new_payload = deepcopy(SIMPLE_PAYLOAD)
    new_payload['attributes']['created'] = "NOW!!!"
    responses.add(responses.POST, f"{host}/foos", json={'data': new_payload})

    foo = Foo.create(attributes={'hello': "world"})

    assert foo.created == "NOW!!!"
    assert foo.a == foo.attributes == {'hello': "world", 'created': "NOW!!!"}


@responses.activate
def test_delete():
    responses.add(responses.DELETE, f"{host}/foos/1")

    foo = Foo(SIMPLE_PAYLOAD)
    foo.delete()

    assert len(responses.calls) == 1
    assert foo.id is None


def test_eq():
    foo = Foo(SIMPLE_PAYLOAD)
    assert foo == {'type': "foos", 'id': "1"}
    assert {'type': "foos", 'id': "1"} == foo
    assert foo == {'data': {'type': "foos", 'id': "1"}}
    assert {'data': {'type': "foos", 'id': "1"}} == foo
    assert foo == Foo(id="1")
    assert Foo(id="1") == foo


def test_as_resource_identifier():
    foo = Foo(SIMPLE_PAYLOAD)
    assert foo.as_resource_identifier() == {'type': "foos", 'id': "1"}


def test_as_relationship():
    foo = Foo(SIMPLE_PAYLOAD)
    assert foo.as_relationship() == {'data': {'type': "foos", 'id': "1"}}
