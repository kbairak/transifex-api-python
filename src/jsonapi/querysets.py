import collections
import urllib

from .requests import _jsonapi_request


class Queryset(collections.abc.Sequence):
    def __init__(self, url, params=None):
        if params is None:
            params = {}

        parsed = urllib.parse.urlparse(url)
        path, query = parsed.path, parsed.query
        query_params = urllib.parse.parse_qs(query)
        query_params = {key: value[0] if len(value) == 1 else value
                        for key, value in list(query_params.items())}

        url = path
        params.update(query_params)

        self._url = url
        self._params = params

        self._data = None
        self._next_url = None
        self._previous_url = None

    @classmethod
    def from_data(cls, response_body):
        result = cls('')
        result._evaluate(response_body)
        return result

    # Evaluate
    @property
    def data(self):
        self._evaluate()
        return self._data

    @property
    def next_url(self):
        self._evaluate()
        return self._next_url

    @property
    def previous_url(self):
        self._evaluate()
        return self._previous_url

    def _evaluate(self, response_body=None):
        from .resources import Resource
        if self._data is not None:
            return

        if response_body is None:
            response_body = _jsonapi_request('get', self._url,
                                             params=self._params)
        included = {}
        if 'included' in response_body:
            included = {(item['type'], item['id']): item
                        for item in response_body['included']}

        self._data = []
        for item in response_body['data']:
            related = {}
            for (name, relationship) in item.get('relationships', {}).items():
                if relationship is None or 'data' not in relationship:
                    continue
                key = (relationship['data']['type'],
                       relationship['data']['id'])
                if key in included:
                    related[name] = Resource.new(included[key])
            self._data.append(Resource.new(related=related, **item))

        self._next_url = response_body.get('links', {}).get('next')
        self._previous_url = response_body.get('links', {}).get('previous')

    # Make it look like a list
    def __getitem__(self, index):
        return self.data[index]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return repr(self.data)

    # Pagination
    def has_next(self):
        return bool(self.next_url)

    def next(self):
        return self.__class__(self.next_url, self._params)

    def has_previous(self):
        return bool(self.previous_url)

    def previous(self):
        return self.__class__(self.previous_url, self._params)

    def all_pages(self):
        if self.data:
            yield self
        page = self
        while page.has_next():
            page = page.next()
            yield page

    def all(self):
        for page in self.all_pages():
            yield from page

    # Filters etc
    def filter(self, **filters):
        from .resources import Resource

        params = dict(self._params)

        for key, value in filters.items():
            key = "filter" + ''.join((f"[{part}]" for part in key.split('__')))
            if isinstance(value, Resource):
                value = value.id

            params[key] = value

        return self.__class__(self._url, params)

    def page(self, *args, **kwargs):
        params = dict(self._params)

        if len(args) == 1 and not kwargs:
            params['page'] = args[0]
        elif len(args) == 0 and kwargs:
            for key, value in kwargs.items():
                params[f'page[{key}]'] = value
        else:
            raise ValueError("Either one positional or keyword arguments "
                             "accepted for pagination")

        return self.__class__(self._url, params)

    def _param_method(field):
        def _method(self, *fields):
            params = dict(self._params)
            params[field] = ','.join(fields)
            return self.__class__(self._url, params)
        return _method

    include = _param_method('include')
    sort = _param_method('sort')
    fields = _param_method('fields')

    def extra(self, **kwargs):
        params = dict(self._params)
        params.update(kwargs)
        return self.__class__(self._url, params)