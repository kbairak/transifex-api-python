- [x] Support non-global setups, both with regards to host/tokens and to
  classes (so that a service can talk to multiple microservices that expose
  {json:api})

- [x] Authentication should store a whole dict which will be merged with
  headers, also it should be able to be dynamic

- [x] Make arguments to bulk operations make more sense

- [ ] Read openapi spec to prefill filters somehow

- [ ] Standardise how the code figures out the nature of JSON objects (whether
  they're singular/plural relationships, API responses etc)

  Example:

  ```python
  # jsonapi/resolvers.py
  def has_data(obj):
      return 'data' in obj

  def has_links(obj):
      return 'links' in obj

  def is_resource_identifier(obj):
      return set(obj.keys()) == {'type', 'id'}

  def is_singular_relationship(obj):
      return has_data(obj) and is_resource_identifier(obj['data'])

  def is_plural_relationship(obj):
      return not has_data(obj) and has_links(obj)
  ```
