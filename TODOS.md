# TODO:

- [ ] Increase test coverage

- [ ] Plural relationships can have a `data` field that is a list

- [ ] Make python 2/3 cross-compatible

- [ ] Handle 204 no content

# Maybe not after all:

- [ ] Read openapi spec to prefill filters somehow

- [ ] Standardise how the code figures out the nature of JSON objects (whether
  they're singular/plural relationships, API responses etc)

  Example:

  ```python
  # jsonapi/utils.py
  def has_data(obj):
      return 'data' in obj

        self.team = Team2.objects.create(organization=self.e2f)
  def has_links(obj):
      return 'links' in obj

  def is_resource_identifier(obj):
      return set(obj.keys()) == {'type', 'id'}

  def is_singular_relationship(obj):
      return has_data(obj) and is_resource_identifier(obj['data'])

  def is_plural_relationship(obj):
      return not has_data(obj) and has_links(obj)
  ```

# DONE:

- [x] Collection URLs can be overriden with a class-variable

- [x] Client-generated IDs can be supported if user calls `.create()` with an
ID kwarg; `save()`ing an object that has an ID will still send a PATCH
request

- [x] Support non-global setups, both with regards to host/tokens and to
  classes (so that a service can talk to multiple microservices that expose
  {json:api})

- [x] Authentication should store a whole dict which will be merged with
  headers, also it should be able to be dynamic

- [x] Make arguments to bulk operations make more sense

- [x] Allow initialization with arbitrary keyword arguments:

  ```python
  Child(name="Maria")
  # Equivalent to
  Child(attributes={'name': "Maria"})

  parent = Parent.get(...)
  Child(parent=parent)
  # Equivalent to
  Child(relationships={'parent': parent})

  Child(parent={'type': "parents", 'id': "1"})
  # Equivalent to
  Child(relationships={'parent': {'type': "parents", 'id': "1"}})

  # If you definitely want something that could be misunderstood, you can fall
  # back to using 'attributes' and 'relationships'

  Child(attributes={'attributes': ["naughty", "tall"]})
  ```
- [x] Drop the `a`, `r` and `R` shortcuts; the field shortcuts make them
      obsolete.
