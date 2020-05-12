import collections

from .requests import _jsonapi_request


def _param_method(field):
    def _method(self, *fields):
        params = dict(self.params)
        params[field] = ','.join(fields)
        return self.__class__(self.klass, params)
    return _method


class Queryset(collections.abc.Sequence):
    def __init__(self, klass, params=None):
        if params is None:
            params = {}

        self.klass = klass
        self.params = params
        self._page = None

    def filter(self, **filters):
        from .jsonapi import Resource

        params = dict(self.params)

        for key, value in filters.items():
            key = "filter" + ''.join((f"[{part}]" for part in key.split('__')))
            if isinstance(value, Resource):
                value = value.id

            params[key] = value

        return self.__class__(self.klass, params)

    def page(self, *args, **kwargs):
        params = dict(self.params)

        if len(args) == 1 and not kwargs:
            params['page'] = args[0]
        elif len(args) == 0 and kwargs:
            for key, value in kwargs.items():
                key = f"page[{key}]"
                params[key] = value
        else:
            raise ValueError("Either one positional or keyword arguments "
                             "accepted for pagination")

        return self.__class__(self.klass, params)

    include = _param_method('include')
    sort = _param_method('sort')
    fields = _param_method('fields')

    def extra(self, **kwargs):
        params = dict(self.params)
        params.update(kwargs)
        return self.__class__(self.klass, params)

    def evaluate(self):
        from .jsonapi import Page

        if self._page is not None:
            return

        url = f"/{self.klass.TYPE}"
        self._page = Page(_jsonapi_request('get', url, params=self.params))

    def __repr__(self):
        self.evaluate()
        return repr(self._page)

    def __getitem__(self, *args, **kwargs):
        self.evaluate()
        return self._page.__getitem__(*args, **kwargs)

    def __len__(self):
        self.evaluate()
        return len(self._page)

    def has_next(self):
        self.evaluate()
        return self._page.has_next()

    def next(self):
        self.evaluate()
        return self._page.next()

    def has_previous(self):
        self.evaluate()
        return self._page.has_previous()

    def previous(self):
        self.evaluate()
        return self._page.previous()

    def all_pages(self):
        self.evaluate()
        return self._page.all_pages()

    def all(self):
        self.evaluate()
        return self._page.all()
