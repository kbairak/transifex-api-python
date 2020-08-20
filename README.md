A python SDK for the [Transifex API (v3)](https://transifex.github.io/openapi/)

## Table of contents

<!--ts-->
* [Table of contents](#table-of-contents)
* [Introduction](#introduction)
* [Installation](#installation)
* [jsonapi usage](#jsonapi-usage)
   * [Setting up](#setting-up)
      * [Registering Resource subclasses](#registering-resource-subclasses)
      * [Customizing setup configuration](#customizing-setup-configuration)
      * [Authentication](#authentication)
   * [Retrieval](#retrieval)
      * [URLs](#urls)
      * [Getting a single resource object from the API](#getting-a-single-resource-object-from-the-api)
      * [Fetching relationships](#fetching-relationships)
      * [Shortcuts](#shortcuts)
      * [Getting Resource collections](#getting-resource-collections)
      * [Prefetching relationships with include](#prefetching-relationships-with-include)
      * [Getting single resource objects using filters](#getting-single-resource-objects-using-filters)
   * [Editing](#editing)
      * [Saving changes](#saving-changes)
      * [Creating new resources](#creating-new-resources)
      * [Deleting](#deleting)
      * [Editing relationships](#editing-relationships)
      * [Bulk operations](#bulk-operations)
      * [Form uploads, redirects](#form-uploads-redirects)
* [transifex_api usage](#transifex_api-usage)
* [Testing](#testing)

<!-- Added by: kbairak, at: Wed 19 Aug 2020 04:17:42 PM EEST -->

<!--te-->

## Introduction

This repository introduces 2 packages: `jsonapi` and `transifex_api`. `jsonapi`
is an _SDK library_ (a library that helps you build SDKs for APIs), targeted at
[{json:api}](https://jsonapi.org/) implementations. `transifex_api` uses
`jsonapi` to create an SDK for the
[Transifex API](https://transifex.github.io/openapi/), with minimal code.

## Installation

```sh
git clone https://github.com/kbairak/transifex-api-python
cd transifex-api-python

python setup.py install
# or
pip install .
# or
pip install -e .  # If you want to work on the SDK's source code
```

## `jsonapi` usage

### Setting up

In order to use `jsonapi`, you need to create a `JsonApi` object that
represents a connection with the API server:

```python
import jsonapi
_api = jsonapi.JsonApi(host="https://api.someservice.com", auth="<API_TOKEN>")
```

#### Registering Resource subclasses

Resource subclasses must be registered to that API instance with:

```python
@_api.register
class Parent(jsonapi.Resource):
    TYPE = "parents"

@_api.register
class Child(jsonapi.Resource):
    TYPE = "children"
```

This is enough to get you started since the library will be able to provide you
with a lot of functionality based on the structure of the responses you get
from the server. Make sure you define and register Resource subclasses for
every type you intend to encounter, because `jsonapi` will use the API
instance's registry to resolve the appropriate subclass the items included in
the API's responses.

#### Customizing setup configuration

The arguments to `JsonApi` are optional. You can add or edit them later using
the `.setup` method (which accepts the same arguments). This way, you can
implement an interface to a server as a library and offer the option to users
to set their authentication method and/or host:

```python
# src/transifex_api/__init__.py

import jsonapi

_api = jsonapi.JsonApi(host="https://rest.api.transifex.com")

@_api.register
class Organization(jsonapi.Resource):
    TYPE = "organizations"

def setup(auth):
    _api.setup(auth=auth)
```

```python
# app.py

import transifex_api

transifex_api.setup("<API_TOKEN>")
organization = transifex_api.Organization.get("1")
...
```

#### Authentication

The `auth` argument to `JsonApi` or `setup` can either be:

1. A string, in which case all requests to the API server will include the
   `Authorization: Bearer <API_TOKEN>` header
2. A callable, in which case the return value is expected to be a dictionary
   which will be merged with the headers of all requests to the API server

   ```python
   import datetime
   import jsonapi
   from .secrets import KEY
   from .crypto import sign

   def myauth():
       return {'x-signature': sign(KEY, datetime.datetime.now())}

   _api = jsonapi.JsonApi(host="https://my.api.com", auth=myauth)
   ```

### Retrieval

#### URLs

By default, collection URLs have the form `/<type>` (eg `/children`) and item
URLs have the form `/<type>/<id>` (eg `/children/1`). This is also part of
{json:api}'s recommendations. If you want to customize them, you need to
override the `get_collection_url` classmethod and the `get_item_url()` method
of the resource's subclass:

```python
@_api.register
class Children(jsonapi.Resource):
    TYPE = "children"

    @classmethod
    def get_collection_url(cls):
        return "/children_collection"

    def get_item_url(self):
        return f"/child_item/{self.id}"
```


#### Getting a single resource object from the API

If you know the ID of the resource object, you can fetch its {json:api}
representation with:

```python
child = Child.get("1")
```

The attributes of a resource object are `id`, `attributes`, `relationships`,
`links` and `related`. `id`, `attributes`, `relationships` and `links` have
exactly the same value as in the API response.

```python
parent = Parent.get("1")
parent.id
# "1"
parent.attributes
# {'name': "Zeus"}
parent.relationships
# {'children': {'links': {'self': "/parent/1/relationships/children",
#                         'related': "/children?filter[parent]=1"}}}

child = Child.get("1")
child.id
# "1"
child.attributes
# {'name': "Hercules"}
child.relationships
# {'parent': {'data': {'type': "parents", 'id': "1"},
#             'links': {'self': "/children/1/relationships/parent",
#                       'related': "/parents/1"}}}
```

You can reload an object from the server by calling `.reload()`:

```python
child.reload()
# equivalent to
child = Child.get(child.id)
```

#### Relationships

##### Intro

We need to talk a bit about how {json:api} represents relationships and how the
`jsonapi` library interprets them. Depending on the value of a field of
`relationships`, we consider the following possibilities. A relationship can
either be:

1. A **null** relationship which will be represented by a null value:

   ```python
   {'type': "children",
    'id': "...",
    'attributes': { ... },
    'relationships': {
        'parent': null,  # <---
        ...,
    },
    'links': { ... }}
   ```

2. A **singular** relationship which will be represented by an object with both
   `data` and `links` fields, with the `data` field being a dictionary:

   ```python
   {'type': "children",
    'id': "...",
    'attributes': { ... },
    'relationships': {
        'parent': {'data': {'type': "parents", 'id': "..."},     # <---
                   'links': {'self': "...", 'related': "..."}},  # <---
        ... ,
    },
    'links': { ... }}
   ```

3. A **plural** relationship which will be represented by an object with a
   `links` field and either a missing `data` field or a `data` field which is a
   list:

   ```python
   {'type': "parents",
    'id': "...",
    'attributes': { ... },
    'relationships': {
        'children': {'links': {'self': "...", 'related': "..."}},  # <---
        ...,
    },
    'links': { ... }}
   ```

   or

   ```python
   {'type': "parents",
    'id': "...",
    'attributes': { ... },
    'relationships': {
        'children': {'links': {'self': "...", 'related': "..."},    # <---
                     'data': [{'type': "children", 'id': "..."},    # <---
                              {'type': "children", 'id': "..."},    # <---
                              ... ]},                               # <---
        ... ,
    },
    'links': { ... }}
   ```

This is important because `jsonapi` will make assumptions about the nature
of relationships based on the existence of these fields.

##### Fetching relationships

The `related` field is meant to host the data of the relationships, **after**
these have been fetched from the API. Lets revisit the last example and inspect
the `relationships` and `related` fields:

```python
parent = Parent.get("1")
parent.relationships
# {'children': {'links': {'self': "/parent/1/relationships/children",
#                         'related': "/children?filter[parent]=1"}}}
parent.related
# {}

child = Child.get("1")
child.relationships
# {'parent': {'data': {'type': "parents", 'id': "1"},
#             'links': {'self': "/children/1/relationships/parent",
#                       'related': "/parents/1"}}}
child.related
# {parent: <Parent: 1 (Unfetched)>}
```

As you can see, the _parent→children_ `related` field is empty while the
_child→parent_ `related` field is prefilled with an "unfetched" Parent
instance. This happens becaue the first one is a _plural_ relationship while
the second is a _singular_ relationship. Unfetched means that we only know its
`id` so far. In both cases, we don't know any meaningful data about the
relationships yet.

In order to fetch the related data, you need to call `.fetch()` with the names
of the relationships you want to fetch:

```python
child.related
# {parent: <Parent: 1 (Unfetched)>}
(child.related['parent'].id,
 child.related['parent'].attributes,
 child.related['parent'].relationships)
# ("1", {}, {})

child.fetch('parent')  # Now `related['parent']` has all the information
child.related
# {parent: <Parent: 1>}
(child.related['parent'].id,
 child.related['parent'].attributes,
 child.related['parent'].relationships)
# ("1",
#  {'name': "Zeus"},
#  {'children': {'links': {'self': "/parent/1/relationships/children",
#                          'related': "/children?filter[parent]=1"}}})

parent.fetch('children')
parent.related
# {'children': [<Child: 1>, <Child: 2>]}
(parent.related['children'][0].id,
 parent.related['children'][0].attributes,
 parent.related['children'][0].relationships)
# ("1",
#  {'name': "Hercules"},
#  {'parent': {'data': {'type': "parents", 'id': "1"},
#              'links': {'self': "/children/1/relationships/parent",
#                        '/parents/1'}}})
```

Trying to fetch an already-fetched relationship will not actually trigger
another request, unless you pass `force=True` to `.fetch()`.

If `.fetch()` is only provided with one positional argument, it will return the
relation:

```python
parent = Parent.get("1")

print(parent.fetch('children')[1].name)
# "Hercules"

# Is equivalent to:

parent.fetch('children')
print(parent.related['children'][1].name)
```

#### Shortcuts

You can access all keys in `attributes` and `related` directly on the resource
object:

```python
child.name == child.attributes['name'] == "Hercules"
# True
```

This is very handy, both for reading and setting values to those fields,
however you should be careful when setting them. If the key is not already part
of `attributes` or `relationships`, the assignment will fall back to the
default operation of Python objects, which is to add the key to the `__dict__`
attribute:

```python
child.__dict__
# {'id': ..., 'attributes': {'name': "Hercules"}, ...}

child.name = "Achilles"
child.__dict__
# {'id': ..., 'attributes': {'name': "Achilles"}, ...}
#                                    ^^^^^^^^^^

child.hair_color = "red"
child.__dict__
# {'id': ..., 'attributes': {'name': "Achilles"}, 'hair_color': "red", ...}
#                                                 ^^^^^^^^^^^^^^^^^^^
```

Be careful of this because the new keys will not be included in subsequent
PATCH operations to update the resource on the server. Normally you won't have
to worry about this since the API server will likely have provided all
attributes and relationships it is likely to accept in subsequent requests,
even if their value is set to `null`. If you definitely want to add a new field
to an object's `attributes` or `relationships`, you can always fall back to
doing so directly:

```python
child.attributes['hair_color'] = "red"
child.__dict__
# {'id': ..., 'attributes': {'name': "Hercules", 'hair_color': "red"}, ...}
#                                                ^^^^^^^^^^^^^^^^^^^
```

#### Getting Resource collections

You can access a collection of resource objects using one of the `list`,
`filter`, `page`, `include`,`sort`, `fields`, `extra`, `all` and `all_pages`
classmethods of Resource subclass.

```python
children = Child.list()
# [<Child: 1>, <Child: 2>, ...]
```

Each method does the following:

- `list` returns the first page of the results

- `filter` applies filters; nested filters are separated by double underscores
  (`__`), Django-style

  | operation         | GET request       |
  |-------------------|-------------------|
  | `.filter(a=1)`    | `?filter[a]=1`    |
  | `.filter(a__b=1)` | `?filter[a][b]=1` |

  _Note: because it's a common use-case, using a resource object as the value
  of a filter operation will result in using its `id` field_

  ```python
  parent = Parent.get("1")

  Child.filter(parent=parent)
  # is equivalent to
  Child.filter(parent=parent.id)
  ```

- `page` applies pagination; it accepts either one positional argument which
  will be passed to the `page` GET parameter or multiple keyword arguments
  which will be passed as nested `page` GET parameters

  | operation         | GET request            |
  |-------------------|------------------------|
  | `.page(1)`        | `?page=1`              |
  | `.page(a=1, b=2)` | `?page[a]=1&page[b]=2` |

  (_Note: you will probably not have to use `.page` yourself since the returned
  lists support pagination on their own, see below_)

- `include` will set the `include` GET parameter; it accepts multiple
  positional arguments which it will join with commas (`,`)

  | operation                   | GET request           |
  |-----------------------------|-----------------------|
  | `.include('parent', 'pet')` | `?include=parent,pet` |

- `sort` will set the `sort` GET parameter; it accepts multiple positional
  arguments which it will join with commas (`,`)

  | operation              | GET request      |
  |------------------------|------------------|
  | `.sort('age', 'name')` | `?sort=age,name` |

- `fields` will set the `fields` GET parameter; it accepts multiple positional
  arguments which it will join with commas (`,`)

  | operation                | GET request        |
  |--------------------------|--------------------|
  | `.fields('age', 'name')` | `?fields=age,name` |

- `extra` accepts any keyword arguments which will be added to the GET
  parameters sent to the API

  | operation                | GET request     |
  |--------------------------|-----------------|
  | `.extra(group_by="age")` | `?group_by=age` |

- `all` returns a generator that will yield all results of a paginated
  collection, using multiple requests if necessary; the pages are fetched
  on-demand, so if you abort the generator early, you will not be performing
  requests against every possible page

- `all_pages` returns a generator of non-empty pages; similarly to `all`, pages
  are fetched on-demand (in fact, `all` uses `all_pages` internally)

All the above methods can be chained to each other. So:

```python
Child.list().filter(a=1)
# is equivalent to
Child.filter(a=1)

Child.filter(a=1).filter(b=2)
# is equivalent to
Child.filter(a=1, b=2)

Child.list().all()
# is equivalent to
Child.all()
```

You can also access pagination via the `has_next`, `has_previous`, `next` and
`previous` methods of a returned list (which is what `all_pages` and `all` use
internally).

All the previous methods also work on plural relationships (assuming the API
supports the applied filters etc on the endpoint specified by the `related`
link of the relationship).

```python

print(parent.fetch('children').filter(name="Hercules")[0].name)

# Will print the names of the *first page* of the children
print([child.name for child in parent.children])
# Will print the names of the *all* the children
print([child.name for child in parent.children.all()])
```

#### Prefetching relationships with `include`

If you use the `include` method on a collection retrieval or if you use the
`include` keyword argument on `.get()` (and if the server supports it), the
included values of the response will be used to prefill the relevant fields of
`related`:

```python
child = Child.get("1", include=['parent'])
child.parent.name  # No need to fetch the parent
# "Zeus"

children = Child.list().include('parent')
[child.parent.name for child in children]  # No need to fetch the parents
# ["Zeus", "Zeus", ...]
```

In case of a plural relationships with a list `data` field, if the response
supplies the related items in the `included` section, these too will be
prefilled.

```python
parent = Parent.get("1", include=['children'])

# Assuming the response looks like:
# {'data': {'type': "parents",
#           'id': "1",
#           'attributes': ...,
#           'relationships': {'children': {'data': [{'type': "children", 'id': "1"},
#                                                   {'type': "children", 'id': "2"}],
#                                          'links': ...}}},
#  'included': [{'type': "children",
#                'id': "1",
#                'attributes': {'name': "Hercules"}},
#               {'type': "children",
#                'id': "2",
#                'attributes': {'name': "Achilles"}}]}

[child.name for child in parent.children]  # No need to fetch
# ["Hercules", "Achilles"]
```

#### Getting single resource objects using filters

Appending `.get()` to a collection will ensure that the collection is of size 1
and return the one resource instance in it. If the collection's size isn't 1,
it will raise a `jsonapi.DoesNotExist` or `jsonapi.MultipleObjectsReturned`
exception accordingly (both are subclasses of `jsonapi.NotSingleItem`).

```python
child = Child.filter(name="Bill").get()
```

The `Resource`'s `.get()` classmethod, which we covered before, also accepts
keyword arguments, if a positional `id` argument isn't used. Calling it this
way, will apply the filters and use the collection's `.get()` method on the
result.

```python
child = Child.get(name="Bill")
# is equivalent to
child = Child.filter(name="Bill").get()
```

_Note: The `Resource`'s `.get()` classmethod accepts an `include` keyword
argument as well, so be careful of naming conflicts if you want to use a filter
called 'include'_

```python
# Don't do this
Child.get(name="Bill", include="parent")
# equivalent to
Child.filter(name="Bill").include('parent').get()

# Do this instead
child = Child.filter(name="Bill", include="parent").get()
```

### Editing

#### Saving changes

After you change some attributes or relationships, you can call `.save()` on an
object, which will trigger a PATCH request to the server. Because usually the
server includes immutable fields with the response (creation timestamps etc),
you don't want to include all attributes and relationships in the request. You
can specify which fields will be sent with:

- `.save()`'s positional arguments, or
- the `EDITABLE` class attribute of the Resource subclass

```python
child = Child.get("1")
child.name += " the Great"
child.save('name')

# or

class Child(Resource):
    TYPE = "children"
    EDITABLE = ['name']

child = Child.get("1")
child.name += " the Great"
child.save()
```

Because setting values right before saving is a common use-case, `.save()` also
accepts keyword arguments. These will be set on the resource object, right
before the actual saving:

```python
child.save(name="Hercules")
# is equivalent to
child.name = "Hercules"
child.save('name')
```

#### Creating new resources

Calling `.save()` on an object whose `id` is not set will result in a POST
request which will (attempt to) create the resource on the server.

```python
parent = Parent.get("1")
child = Child(attributes={'name': "Hercules"},
              relationships={'parent': parent})
child.save()
```

After saving, the object will have the `id` returned by the server, plus any
other server-generated attributes and relationships (for example, creation
timestamps).

There is a shortcut for the above, called `.create()`

```python
parent = Parent.get("1")
child = Child.create(attributes={'name': "Hercules"},
                     relationships={'parent': parent})
```

_Note: for relationships, you can provide either a resource instance, a
"Resource Identifier" (the 'data' value of a relationship object) or an entire
relationship from another resource. So, the following are equivalent:_

```python
# Well, almost equivalent, the first example will trigger a request to fetch
# the parent's data from the server
child = Child.create(attributes={'name': "Hercules"},
                     relationships={'parent': Parent.get("1")})
child = Child.create(attributes={'name': "Hercules"},
                     relationships={'parent': Parent(id="1")})
child = Child.create(attributes={'name': "Hercules"},
                     relationships={'parent': {'type': "parents": 'id': "1"}})
child = Child.create(attributes={'name': "Hercules"},
                     relationships={'parent': {'data': {'type': "parents": 'id': "1"}}})
```


This way, you can reuse a relationship from another object when creating,
without having to fetch the relationship:

```python
new_child = Child.create(attributes={'name': "Achilles"},
                         relationships={'parent': old_child.parent})
```

##### Magic kwargs

When making new (unsaved) instances, or when you create instances on the server
with `.create()`, you can supply any keword argument apart from `id`,
`attributes`, `relationships`, etc and they will be interpreted as attributes
or relationships. Anything that looks like a relationship will be interpreted
as such while everything else will be interpreted as an attribute.

Things that are interpreted as relationships are:

- Resource instances
- Resource identifiers - dictionaries with 'type' and 'id' fields
- Relationship objects - dictionaries with a single 'data' field whose value is
  a resource identifier

So

```python
Child(name="Hercules")
# is equivalent to
Child(attributes={'name': "Hercules"})

Child(parent={'type': "parents", 'id': "1"})
# is equivalent to
Child(relationships={'parent': {'type': "parents", 'id': "1"}})

Child(parent=Parent(id="1"))
# is equivalent to
Child(relationships={'parent': Parent(id="1")})
```

If you are worried about naming conflicts, for example if you want to have a
relationship called 'attributes', an attribute that looks like a relationship
and an attribute called 'id', you should back to using 'attributes' and
'relationships' directly.

```python
# Don't do this
child = Child(attributes={'type': "attributes", 'id': "1"},
              stats={'type': "stats", 'id': "2"},
              id="3")
child.to_dict()
# {'type': "children",
#  'attributes': {'type': "attributes", 'id': "1"},
#  'relationships': {'stats': {'data': {'type': "stats", 'id': "2"}}},
#  'id': "3"}

# Do this instead
child = Child(relationships={'attributes': {'type': "attributes", 'id': "1"}},
              attributes={'stats': {'type': "stats", 'id': "2"},
                          'id': "3"})
child.to_dict()
# {'type': "children",
#  'attributes': {'stats': {'type': "stats", 'id': "2"},
#                 'id': "3"},
#  'relationships': {'attributes': {'data': {'type': "attributes", 'id': "1"}}}}
```

_Note: `.to_dict()` returns the {json:api} representation of the Resource
instance, ie what the payload to the server would be if we called `.save()` on
it_

##### Client-generated IDs

Since `.save()` will issue a PATCH request when invoked on objects that have an
ID, if you want to supply your own client-generated ID during creation, you
**have** to use `.create()`, which will always issue a POST request.

```python
Child(attributes={'name': "Hercules"}).save()
# POST: {data: {type: "children", attributes: {name: "Hercules"}}}

Child(id="1", attributes={'name': "Hercules"}).save()
# PATCH: {data: {type: "children", id: "1", attributes: {name: "Hercules"}}}

Child.create(attributes={'name': "Hercules"})
# POST: {data: {type: "children", attributes: {name: "Hercules"}}}

Child.create(id="1", attributes={'name': "Hercules"})
# POST: {data: {type: "children", id: "1", attributes: {name: "Hercules"}}}
# ^^^^
```


#### Deleting

Deleting happens simply by calling `.delete()` on an object. After deletion,
the object will have the same data as before, except its `id` will be set to
`None`. This happens in case you want to delete an object and instantly
re-create it, with a different ID.

```python
child = Child.get("1")
child.delete()

# Will create a new child with the same name and parent as the previous one
child.save('name', 'parent')

child.id in (None, "1")
# False
```

#### Editing relationships

##### Singular relationships

Changing a singular relationship can happen in two ways (this also depends on
what the server supports).

```python
child = Child.get("1")

child.parent = new_parent
child.save('parent')

# or

child.change('parent', new_parent)
```

The first one will send a PATCH request to `/children/1` with a body of:

```json
{"data": {"type": "children",
          "id": "1",
          "relationships": {"parent": {"data": {"type": "parents", "id": "2"}}}}}
```

The second one will send a PATCH request to the URL indicated by
`child.relationships['parent']['links']['self']`, which will most likely be
something like `/children/1/relationships/parent`, with a body of:

```json
{"data": {"type": "parents", "id": "2"}}
```

If you want to use the first way, you could also change the relationship
directly:

```python
child.relationships['parent'] = {'data': {'type': "parents", 'id': "2"}}

child.save('parent')
```

However, this poses a danger. `relationships` and `related` are supposed to be
in sync with each other and, if you change one or the other directly, they may
stop being in sync which may generate some confusion later. A successful
`.save()` will rewrite the relationships so you should be OK. However, if you
want to be safe, you should use the `.set_related()` method to edit
relationships:

```python
child.set_related('parent', Parent(id="2"))
```

or use the relationship's name shortcut:

```python
child.parent = Parent(id="2")
```

(the shortcut uses `.set_related()` during assignment internally anyway)

##### Plural relationships

For changing plural relationships, you can use one of the `add`, `remove` and
`reset` methods:

```python
parent = Parent.get("1")
parent.add('children', [new_child, ...])
parent.remove('children', [existing_child, ...])
parent.reset('children', [child_a, child_b, ...])
```

These will send a POST, DELETE or PATCH request respectively to the URL
indicated by `parent.relationships['children']['links']['self']`, which will
most likely be something like `/parents/1/relationships/children`, with a body
of:

```json
{"data": [{"type": "children", "id": "1"},
          {"type": "children", "id": "2"},
          {"...": "..."}]}
```

Similar to the case when we were instanciating objects with relationships, the
values passed to the above methods can either be resource objects, "resource
identifiers" or entire relationship objects:

```python
parent.add('children', [Child.get("1"),
                        Child(id="2"),
                        {'type': "children", 'id': "3"},
                        {'data': {'type': "children", 'id': "4"}}])
```

This way, you can easily use another object's plural relationship:

```python
parent_a = Parent.get('1')
parent_b = Parent.get('2')

# Make sure 'parent_b' has the same children as 'parent_a'
parent_b.reset('children', list(parent_a.fetch('children').all()))
```

#### Bulk operations

Resource subclasses provide the `bulk_delete`, `bulk_create` and `bulk_update`
classmethods for API endpoints that support such operations. The arguments to
these class methods are quite flexible. Consult the docstrings of each method
for their types or see the following examples.

Furthermore, `bulk_update` accepts a `fields` keyword argument with the
`attributes` and `relationships` of the objects it will attempt to update.

```python
# Bulk-create
Child.bulk_create([Child(attributes={'name': "One"},
                         relationships={'parent': parent}),
                   {'attributes': {'name': "Two"},
                    'relationships': {'parent': parent}},
                   ({'name': "Three"}, {'parent': parent})])

# Bulk-update
child_a = Child.get("a")
child_a.married = True

Child.bulk_update([child_a,
                   {'id': "b", 'attributes': {'married': True}},
                   ("c", {'married': True}),
                   "d"],
                  fields=['married'])

# Bulk delete
child_a = Child.get("a")
Child.bulk_delete([child_a, {'id': "b"}, "c"])

parent = Parent.get("1")
Child.delete(list(parent.children.all()))
```

For more details, see our
[bulk oprations {json:api} profile](https://github.com/transifex/openapi/blob/devel/txapi_spec/bulk_profile.md).

#### Form uploads, redirects

If an endpoint accepts other content-types apart from
`application/vnd.api+json` during creation (most likely a `multipart/form-data`
for file uploads), you can perform such requests using the `.create_with_form`
classmethod. The keyword arguments you provide will be passed to the `requests`
library, giving you complete control over the request you want to perform.

According to {json:api}'s recommendations, an endpoint may return a
303-redirect response. If that's the case for a `.get()` or `.reload()` call,
the object's `id`, `attributes`, `links`, `relationships` and `related`
attributes will be empty. What will be there is a `redirect` attribute set to
the response's `Location` header's value. Calling `.follow()` on such an object
will retrieve that location and process the response using the appropriate
class.

Given these two mechanisms, here is how you might go about performing a
[source file upload](https://transifex.github.io/openapi/#tag/Resource-Strings/paths/~1resource_strings_async_uploads/post)
in Transifex API:

```python
class TxResource(Resource)
    TYPE = "resources"
class ResourceStringsAsyncUpload(Resource)
    TYPE = "resource_strings_async_uploads"
class ResourceString(Resource)
    TYPE = "resource_strings"

resource = TxResource.get(...)
with open(...) as f:
    upload = ResourceStringsAsyncUpload.create_with_form(
        data={'resource': resource.id},
        files={'content': f},
    )
while True:
    if upload.redirect:
        strings = upload.follow()
        break
    sleep(5)
    upload.reload()
```

## `transifex_api` usage

As we said before, the `transifex_api` package has minimal code as almost the
entire functionality is implemented in `jsonapi`. `transifex_api` simply hosts
the Resource subclasses. You can find them
[here](src/transifex_api/__init__.py)
and cross-check with the
[API specification](https://transifex.github.io/openapi/). Assuming you
understand how the `jsonapi` package works, you should be able to work with
`transifex_api`.

Sample usage:

```python
import os
import transifex_api

# There is a default host for transifex
transifex_api.setup(os.environ['API_TOKEN'])

organizations = {organization.slug: organization
                 for organization in transifex_api.Organization.all()}
organization = organizations['kb_org']

project = transifex_api.Project.get(organization=organization, slug="kb1")

resource = Resource.get(project=project, slug="fileless")

languages = {language.code: language
             for language in project.fetch('languages').all()}
language = languages['el']

translations = ResourceTranslation.\
    filter(resource=resource, language=language).\
    include('resource_string')
translation = translations[0]

# Let's translate something
if not translation.strings:
    source_string = translation.resource_string.strings['other']
    translation.strings = {'other': source_string + " in greeeek!!!"}
if not translation.reviewed:
    translation.reviewed = True
translation.save('strings', 'reviewed')
```


## Testing

To run the tests:

```sh
mkvirtualenv transifex_sdk
pip install -e .
pip install -r requirements/testing.txt
make test
```

There are several variations on test commands, most targeted towards active
development:


- `make test`: Run tests in multiple python versions using
  [tox](https://tox.readthedocs.io/en/latest/)
- `make covtest`: Display coverage information using
  [pytest-cov](https://github.com/pytest-dev/pytest-cov)
- `make debugtest`: Disable screen capture (with `-s` option to pytest) so that
  you can invoke a debugger while the tests are running
- `make watchtest`: Invoke the tests with
  [pytest-watch](https://github.com/joeyespo/pytest-watch) so that they rerun
  every time a source python file in the repository changes
