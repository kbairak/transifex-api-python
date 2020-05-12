import json
from copy import deepcopy

import responses
import transifex_api
from transifex_api.jsonapi import Resource

from .payloads import Payloads

transifex_api.setup("test_api_key")


class Child(Resource):
    TYPE = "children"


class Parent(Resource):
    TYPE = "parents"


child_payloads = Payloads(
    'children', 'child',
    extra={'relationships': {
        'parent': {'data': {'type': "parents", 'id': "1"},
                   'links': {'self': "/children/1/relationships/parent",
                             'related': "/parents/1"}},
    }}
)
parent_payloads = Payloads(
    'parents',
    extra={'relationships': {
        'children': {'links': {'self': "/parents/1/relationships/children",
                               'related': "/parents/1/children"}},
    }}
)


@responses.activate
def test_singular_fetch():
    responses.add(responses.GET, "https://rest.api.transifex.com/parents/1",
                  json={'data': parent_payloads[1]})

    child = Child(child_payloads[1])

    assert (child.R ==
            child.relationships ==
            {'parent': {'data': {'type': "parents", 'id': "1"},
                        'links': {'self': "/children/1/relationships/parent",
                                  'related': "/parents/1"}}})
    assert (child.r['parent'] ==
            child.related['parent'] ==
            child.parent ==
            Parent(id="1"))
    assert child.parent.a == child.parent.attributes == {}

    child.fetch('parent')

    assert len(responses.calls) == 1
    assert (child.r['parent'] ==
            child.related['parent'] ==
            child.parent ==
            Parent(id="1"))
    assert child.parent.a == child.parent.attributes == {'name': "parent 1"}
    assert child.parent.name == "parent 1"


@responses.activate
def test_fetch_plural():
    responses.add(
        responses.GET,
        "https://rest.api.transifex.com/parents/1/children",
        json={'data': child_payloads[1:4],
              'links': {'next': "/parents/1/children?page=2"}},
        match_querystring=True,
    )
    responses.add(
        responses.GET,
        "https://rest.api.transifex.com/parents/1/children?page=2",
        json={'data': child_payloads[4:7],
              'links': {'previous': "/parents/1/children?page=1"}},
        match_querystring=True,
    )

    parent = Parent(parent_payloads[1])
    assert 'children' not in parent.r
    parent.fetch('children')

    assert len(responses.calls) == 1
    assert 'children' in parent.r
    assert len(parent.children) == 3
    assert isinstance(parent.children[0], Child)
    assert parent.children[1].id == "2"
    assert parent.children[2].name == "child 3"

    assert parent.children.has_next()
    assert not parent.children.has_previous()
    assert len(list(parent.children.all())) == 6


@responses.activate
def test_change_parent_with_save():
    response_body = deepcopy(child_payloads[1])
    relationship = response_body['relationships']['parent']
    relationship['data']['id'] = 2
    relationship['links']['related'] = relationship['links']['related'].\
        replace('1', '2')

    responses.add(responses.PATCH, "https://rest.api.transifex.com/children/1",
                  json={'data': response_body})

    child = Child(child_payloads[1])
    child.parent = Parent(parent_payloads[2])

    assert child.R['parent']['data']['id'] == "2"
    assert child.r['parent'].id == child.parent.id == "2"

    child.save()

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert (json.loads(call.request.body)['data']
            ['relationships']['parent']['data']['id'] ==
            "2")


@responses.activate
def test_change_parent_with_change():
    responses.add(
        responses.PATCH,
        "https://rest.api.transifex.com/children/1/relationships/parent",
    )

    child = Child(child_payloads[1])
    new_parent = Parent(id="2")
    child.change('parent', new_parent)

    assert child.R['parent']['data']['id'] == "2"
    assert child.parent.id == "2"
    assert child.parent == new_parent

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert json.loads(call.request.body) == new_parent.as_relationship()
