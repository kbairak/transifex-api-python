# transifex-api-python

A python SDK for the [Transifex API (v3)](https://transifex.github.io/openapi/)

## Table of contents

<!--ts-->
* [Introduction](#introduction)
* [Transifex-flavored {json:api}](#transifex-flavored-jsonapi)
* [Installation](#installation)
* [jsonapi usage](#jsonapi-usage)
   * [Setting up](#setting-up)
   * [Getting a single resource object from the API](#getting-a-single-resource-object-from-the-api)
   * [Fetching relationships](#fetching-relationships)
   * [Shortcuts](#shortcuts)
   * [Getting many resource objects at the same time](#getting-many-resource-objects-at-the-same-time)
   * [Prefetching relationships with include](#prefetching-relationships-with-include)
   * [Saving changes, creating new resources](#saving-changes-creating-new-resources)
   * [Deleting](#deleting)
   * [Editing relationships](#editing-relationships)
   * [Bulk operations](#bulk-operations)
   * [Form uploads, redirects](#form-uploads-redirects)
* [transifex_api usage](#transifex_api-usage)
* [Tests](#tests)

<!-- Added by: kbairak, at: Mon 25 May 2020 11:40:31 PM EEST -->

<!--te-->

## Introduction

This repository introduces 2 packages: `jsonapi` and `transifex_api`. `jsonapi`
is an _SDK library_ (a library that helps you build SDKs for APIs), targeted at
[{json:api}](https://jsonapi.org/) implementations. `transifex_api` uses
`jsonapi` to create an SDK for the
[Transifex API](https://transifex.github.io/openapi/), with minimal code.

## Transifex-flavored {json:api}

Our `jsonapi` library implementation assumes that the API in question follows
all guidelines of the {json:api} specification, plus a few more that are not
universal. We call these extra guidelines: **_Transifex-flavored {json:api}_**
and they consist of the following:

1. A resource's relationship to another can either be:

   1. A **singular-null** relationship which will be represented by a null
      value:

      ```json
      {"type": "children",
       "id": "...",
       "data": {"...": "..."},
       "relationships": {"parent": null,
                         "...": {"...": "..."}},
       "data": {"...": "..."}}
      ```

   2. A **singular-non-null** relationship which will be represented by an
      object with both `data` and `links` fields:

      ```json
      {"type": "children",
       "id": "...",
       "data": {"...": "..."},
       "relationships": {"parent": {"data": {"type": "parents", "id": "..."},
                                    "links": {"self": "...", "related": "..."}},
                         "...": {"...": "..."}},
       "data": {"...": "..."}}
      ```

   3. A **plural** relationship which will be represented by an object with a
      `links` field and **without** a `data` field:

      ```json
      {"type": "parents",
       "id": "...",
       "data": {"...": "..."},
       "relationships": {"children": {"links": {"self": "...", "related": "..."}},
                         "...": {"...": "..."}},
       "data": {"...": "..."}}
      ```

   This is important because `jsonapi` will make assumptions about the nature
   of relationships based on the existence of these fields.

2. Collection endpoints always have the form `/<type>` and all resource
   endpoints always have the form `/<type>/<id>` (this is not required by the
   {json:api} specification, but is recommended)

3. Client-generated IDs are not supported, ie if a resource on the SDK's side
   has a non-null ID field, then it will be considered pre-existing (`.save()`
   will trigger a PATCH request) and if it doesn't, it will be considered
   unsaved (`.save()` will trigger a POST request)

4. The API may support bulk operations, which use the
   `application/vnd.api+json;profile="bulk"` Content-Type, as described by our
   [bulk operations {json:api} profile](https://github.com/transifex/openapi/blob/devel/txapi_spec/bulk_profile.md)

5. Authorization is done via the `Authorization` HTTP header


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

Before using `jsonapi`, you need to setup the connection with the API server.
This is done with:

```python
import jsonapi

jsonapi.setup("<API_TOKEN>", "https://api.someservice.com")
```

The first argument is either:

1. A string, in which case the value of the `Authorization` header sent with
   every request will be `Bearer <API_TOKEN>`, or

2. Any callable object in which case its return value will be used for the
   `Authorization` header

Creating a class for an API resource which follows the {json:api} and the above
guidelines is as simple as:

```python
import jsonapi

class Parent(jsonapi.Resource):
    TYPE = "parents"

class Child(jsonapi.Resource):
    TYPE = "children"
```

`jsonapi` maintains a global registry which maps `TYPE` strings to Resource
subclasses, so make sure you have imported all class definitions you intend to
use in order for `jsonapi` to be able to map relationships and included data to
the relevant classes.

### Getting a single resource object from the API

If you know the ID of the resource object, you can fetch its {json:api}
representation with:

```python
child = Child.get("1")
```

The attributes of a resource object are `id`, `attributes`, `relationships`,
`links` and `related`. `id`, `attributes`, `relationships` and `links` have
exactly the same value as in the API response. `related` can eventually hold
information about the resource's relationships, after they are fetched with
`.fetch()`.

```python
parent = Parent.get("1")
parent.id
# "1"
parent.attributes
# {'name': "Zeus"}
parent.relationships
# {'children': {'links': {'self': "/parent/1/relationships/children",
#                         'related': "/children?filter[parent]=1"}}}
parent.related
# {}

child = Child.get("1")
child.id
# "1"
child.attributes
# {'name': "Hercules"}
child.relationships
# {'parent': {'data': {'type': "parents", 'id': "1"},
#             'links': {'self': "/children/1/relationships/parent",
#                       'related': "/parents/1"}}}
child.related
# {'parent': <Parent: 1>}
```

_Reminding that plural relationships only have the `links` field while singular
relationships have both `links` and `data`. This way, `jsonapi` is able to tell
that the relationship between `Parent` and `Child` is one-to-many._

You can reload an object from the server by calling `.reload()`:

```python
child.reload()
# equivalent to
child = Child.get(child.id)
```

In the last example, you may have noticed that `child.related` is not empty.
This happens with singular relationships. If you look closely, however, you
will see that apart from the `id`, the related parent doesn't have any other
data. The rest of the data can be fetched with `.fetch()`, as for the plural
relationships.

```python
(child.related['parent'].id,
 child.related['parent'].attributes,
 child.related['parent'].relationships)
# ("1", {}, {})
```

### Fetching relationships

In order to fetch related data, you need to call `.fetch()` with the names of
the relationships you want to fetch:

```python
child.fetch('parent')  # Now `related['parents']` has all the information
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

### Shortcuts

Because `attributes`, `related` and `relationships` are so important, resource
objects have the `a`, `r` and `R` shortcuts respectively (`related` is slightly
more useful than `relationships` so the easier `r` shortcut was chosen for it).

```python
child.a == child.attributes
# True
child.r == child.related
# True
child.R == child.relationships
# True
```

Furthermore, you can access all keys in `attributes` and `related` directly on
the resource object:

```python
child.name == child.attributes['name'] == child.a['name'] == "Hercules"
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
child.attrbutes['hair_color'] = "red"
# or
child.a['hair_color'] = "red"
```

### Getting many resource objects at the same time

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

### Prefetching relationships with `include`

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

### Saving changes, creating new resources

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

As mentioned before, calling `.save()` on an object whose `id` is not set will
result in a POST request which will (attempt to) create the resource on the
server.

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
new_child = Child.create(attrbutes={'name': "Achilles"},
                         relationships={'parent': old_child.parent})
```

### Deleting

Deleting happens simply by calling `.delete()` on an object. After deletion,
the object will have the same data as before, except its `id` is set to `None`.
This happens in case you want to delete an object and instantly re-create it,
with a different ID.

```python
child = Child.get("1")
child.delete()

# Will create a new child with the same name and parent as the previous one
child.save('name', 'parent')

child.id in (None, "1")
# False
```

### Editing relationships

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
# or
child.R['parent'] = {'data': {'type': "parents", 'id': "2"}}

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

### Bulk operations

Resource subclasses provide the `bulk_delete`, `bulk_create` and `bulk_update`
classmethods for API endpoints that support such operations. The arguments to
these class methods are lists of:

- resource objects
- dictionaries with optional `attributes`, `relationships` and `id` keys
- 3-tuples of `attributes`, `relationships` and `id`
- 2-tuples of `attributes` and`relationships`
- `attributes` dictionaries

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
                   {'attributes': {'married': True}, 'id': "b"},
                   ({'married': True}, None, "c")],
                  fields=['married'])

# Bulk delete
child_a = Child.get("a")
Child.bulk_delete([child_a, {'id': "b"}, (None, None, "c")])

parent = Parent.get("1")
Child.delete(list(parent.children.all()))
```

For more details, see our
[bulk oprations {json:api} profile](https://github.com/transifex/openapi/blob/devel/txapi_spec/bulk_profile.md).

### Form uploads, redirects

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

projects = transifex_api.Project.filter(organization=organization, slug="kb1")
project = projects[0]

resources = {resource.slug: resource
             for resource in Resource.filter(project=project).all()}
resource = resources['fileless']

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


## Tests

To run the tests:

```sh
mkvirtualenv transifex_sdk
pip install -e .
pip install -r requirements/testing.txt
make test
```
