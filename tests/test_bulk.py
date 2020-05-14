import json
import responses
import transifex_api
from transifex_api.jsonapi import Resource

from .constants import host
from .payloads import Payloads

transifex_api.setup("test_api_key")


class BulkItem(Resource):
    TYPE = "bulk_items"


payloads = Payloads('bulk_items')


@responses.activate
def test_bulk_delete():
    responses.add(responses.DELETE, f"{host}/bulk_items")

    items = [BulkItem(payload) for payload in payloads[1:4]]
    BulkItem.bulk_delete([items[0],
                          items[1].as_resource_identifier(),
                          items[2].as_relationship()])

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert (call.request.headers['Content-Type'] ==
            'application/vnd.api+json;profile="bulk"')
    assert (json.loads(call.request.body)['data'] ==
            [{'type': "bulk_items", 'id': str(i)} for i in range(1, 4)])


@responses.activate
def test_bulk_create():
    response_payload = payloads[1:6]
    for item, when in zip(response_payload, range(5)):
        item['attributes']['created'] = f"now + {when}"
    responses.add(responses.POST, f"{host}/bulk_items",
                  json={'data': response_payload})

    result = BulkItem.bulk_create([
        BulkItem(attributes={'name': "bulk_item 1"}),
        {'attributes': {'name': "bulk_item 2"}},
        ({'name': "bulk_item 3"}, None, None),
        ({'name': "bulk_item 4"}, None),
        {'name': "bulk_item 5"},
    ])

    assert len(responses.calls) == 1
    call = responses.calls[0]
    assert (call.request.headers['Content-Type'] ==
            'application/vnd.api+json;profile="bulk"')
    assert (json.loads(call.request.body) ==
            {'data': [{'type': "bulk_items",
                       'attributes': {'name': f"bulk_item {i}"}}
                      for i in range(1, 6)]})

    assert isinstance(result[0], BulkItem)
    assert result[1].id == "2"
    assert result[2] == BulkItem(id="3")

    for i in range(5):
        assert result[i].id == str(i + 1)
        assert result[i].name == result[i].a['name'] == f"bulk_item {i + 1}"
        assert result[i].created == result[i].a['created'] == f"now + {i}"
