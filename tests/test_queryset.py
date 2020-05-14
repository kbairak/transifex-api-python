import responses
import transifex_api
from transifex_api.jsonapi import Resource
from transifex_api.queryset import Queryset

from .payloads import Payloads

transifex_api.setup("test_api_key")


class Item(Resource):
    TYPE = "items"


payloads = Payloads('items')


@responses.activate
def test_queryset():
    responses.add(responses.GET, 'https://rest.api.transifex.com/items',
                  json={'data': payloads[1:4]})

    queryset = Queryset('/items')
    list(queryset)

    assert len(queryset) == 3
    assert isinstance(queryset[0], Item)
    assert queryset[1].id == "2"
    assert queryset[2].name == "item 3"

    assert not queryset.has_next()
    assert not queryset.has_previous()

    assert list(queryset) == list(queryset.all())


def test_from_data():
    queryset = Queryset.from_data({'data': payloads[1:4]})

    assert len(queryset) == 3
    assert isinstance(queryset[0], Item)
    assert queryset[1].id == "2"
    assert queryset[2].name == "item 3"

    assert not queryset.has_next()
    assert not queryset.has_previous()

    assert list(queryset) == list(queryset.all())


@responses.activate
def test_pagination():
    responses.add(responses.GET, "https://rest.api.transifex.com/items?page=2",
                  json={'data': payloads[4:7],
                        'links': {'previous': "/items?page=1"}}, status=200)

    first_page = Queryset.from_data({'data': payloads[1:4],
                                     'links': {'next': "/items?page=2"}})
    assert first_page.has_next()
    second_page = first_page.next()
    list(second_page)

    assert len(responses.calls) == 1

    assert len(second_page) == 3
    assert isinstance(second_page[0], Item)
    assert second_page[1].id == "5"
    assert second_page[2].name == "item 6"

    assert not second_page.has_next()
    assert second_page.has_previous()

    assert list(first_page.all()) == list(first_page) + list(second_page)
    assert ([list(page) for page in first_page.all_pages()] ==
            [list(first_page), list(second_page)])


@responses.activate
def test_all():
    responses.add(responses.GET, "https://rest.api.transifex.com/items",
                  json={'data': payloads[1:4]}, status=200)
    queryset = Item.list()

    assert len(queryset) == 3
    assert isinstance(queryset[0], Item)
    assert queryset[1].id == "2"
    assert queryset[2].name == "item 3"

    assert not queryset.has_next()
    assert not queryset.has_previous()

    assert list(queryset) == list(queryset.all())


@responses.activate
def test_all_with_pagination():
    responses.add(responses.GET, "https://rest.api.transifex.com/items",
                  json={'data': payloads[1:4],
                        'links': {'next': "/items?page=2"}}, status=200,
                  match_querystring=True)
    responses.add(responses.GET, "https://rest.api.transifex.com/items?page=2",
                  json={'data': payloads[4:7],
                        'links': {'previous': "/items?page=1"}}, status=200,
                  match_querystring=True)

    first_page = Item.list()

    assert first_page.has_next()
    second_page = first_page.next()
    list(second_page)

    assert len(responses.calls) == 2

    assert len(second_page) == 3
    assert isinstance(second_page[0], Item)
    assert second_page[1].id == "5"
    assert second_page[2].name == "item 6"

    assert not second_page.has_next()
    assert second_page.has_previous()

    assert list(first_page.all()) == list(first_page) + list(second_page)
    assert ([list(page) for page in first_page.all_pages()] ==
            [list(first_page), list(second_page)])


@responses.activate
def test_filter():
    responses.add(responses.GET, "https://rest.api.transifex.com/items",
                  json={'data': payloads[1:5]}, status=200,
                  match_querystring=True)
    responses.add(responses.GET,
                  "https://rest.api.transifex.com/items?filter[odd]=1",
                  json={'data': payloads[1:5:2]}, status=200,
                  match_querystring=True)

    all_items = Item.list()
    odd_items = Item.filter(odd=1)

    assert len(all_items) == 4
    assert len(odd_items) == 2

    assert list(odd_items) == [all_items[0], all_items[2]]

    assert (list(Item.filter(odd=1)) ==
            list(Item.list().filter(odd=1)) ==
            list(Item.filter(odd=2).filter(odd=1)))
