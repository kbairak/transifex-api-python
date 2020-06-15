import json

import jsonapi
import responses

from .constants import host
from .payloads import Payloads

_api = jsonapi.JsonApi(host=host, auth="test_api_key")


@_api.register
class BulkItem(jsonapi.Resource):
    TYPE = "bulk_items"


payloads = Payloads('bulk_items')


@responses.activate
def test_bulk_delete():
    responses.add(responses.DELETE, f"{host}/bulk_items")

    items = [BulkItem(payload) for payload in payloads[1:6]]
    BulkItem.bulk_delete([items[0],
                          items[1].as_resource_identifier(),
                          items[2].as_relationship(),
                          items[3].id])

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert (call.request.headers['Content-Type'] ==
            'application/vnd.api+json;profile="bulk"')
    assert (json.loads(call.request.body)['data'] ==
            [{'type': "bulk_items", 'id': str(i)} for i in range(1, 5)])


@responses.activate
def test_bulk_create():
    response_payload = payloads[1:5]
    for item, when in zip(response_payload, range(1, 5)):
        item['attributes']['created'] = f"now + {when}"
    responses.add(responses.POST, f"{host}/bulk_items",
                  json={'data': response_payload})

    result = BulkItem.bulk_create([
        BulkItem(attributes={'name': "bulk_item 1"}),
        {'attributes': {'name': "bulk_item 2"}},
        ({'name': "bulk_item 3"}, None),
        {'name': "bulk_item 4"},
    ])

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert (call.request.headers['Content-Type'] ==
            'application/vnd.api+json;profile="bulk"')
    assert (json.loads(call.request.body) ==
            {'data': [{'type': "bulk_items",
                       'attributes': {'name': f"bulk_item {i}"}}
                      for i in range(1, 5)]})

    assert isinstance(result[0], BulkItem)
    assert result[1].id == "2"
    assert result[2] == BulkItem(id="3")

    for i in range(4):
        assert result[i].id == str(i + 1)
        assert result[i].name == result[i].a['name'] == f"bulk_item {i + 1}"
        assert result[i].created == result[i].a['created'] == f"now + {i + 1}"


@responses.activate
def test_bulk_update():
    response_payload = payloads[1:6]
    for item, when in zip(response_payload, range(1, 6)):
        item['attributes'].update({'last_update': f"now + {when}",
                                   'name': f"modified name {when}"})
    responses.add(responses.PATCH, f"{host}/bulk_items",
                  json={'data': response_payload})

    result = BulkItem.bulk_update([
        BulkItem(id="1", attributes={'name': "modified name 1"}),
        {'id': "2", 'attributes': {'name': "modified name 2"}},
        ("3", {'name': "modified name 3"}, None),
        ("4", {'name': "modified name 4"}),
        "5",
    ])

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert (call.request.headers['Content-Type'] ==
            'application/vnd.api+json;profile="bulk"')
    assert (json.loads(call.request.body) ==
            {'data': ([{'type': "bulk_items",
                        'id': str(i),
                        'attributes': {'name': f"modified name {i}"}}
                       for i in range(1, 5)] +
                      [{'type': "bulk_items", 'id': "5"}])})

    assert isinstance(result[0], BulkItem)
    assert result[1].id == "2"
    assert result[2] == BulkItem(id="3")
    assert result[3].name == "modified name 4"

    for i in range(5):
        assert result[i].id == str(i + 1)
        assert (result[i].name ==
                result[i].a['name'] ==
                f"modified name {i + 1}")
        assert (result[i].last_update ==
                result[i].a['last_update'] ==
                f"now + {i + 1}")
