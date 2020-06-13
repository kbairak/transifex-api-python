- [ ] Support non-global setups, both with regards to host/tokens and to
  classes (so that a service can talk to multiple microservices that expose
  {json:api})

  Example:

  ```python
  # src/jsonapi/__init__.py

  from .apis import JsonApi
  from .resources import Resource
  ```

  ```python
  # src/jsonapi/apis.py

  class JsonApi:
      def __init__(self, host=None, auth=None):
          self.registry = {}
          self.setup(host, auth)

      def setup(self, host=None, auth=None):
          if auth is not None:
              if callable(auth, str):
                  auth = auth()
              self.auth_header = f"Bearer {auth}"

          if host is not None:
              self.host = host

      def register(self, cls):
          self.registry[cls.TYPE] = cls
          cls.REGISTRY = self.registry
  ```

  ```python
  # src/transifex_api.py

  from transifex.jsonapi import JsonApi, Resource
  _api = JsonApi('https://rest.api.transifex.com')

  @_api.register
  class Organization(Resource):
      TYPE = "organizations"

  setup = _api.setup
  ```

  ```python
  # app.py

  import transifex_api
  transifex_api.setup('<api-token>')
  org = transifex_api.Organization.get('1')
  ```

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

- [ ] Make arguments to bulk operations make more sense

- [ ] Read openapi spec to prefill filters somehow
