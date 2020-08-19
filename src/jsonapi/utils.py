import collections


def is_resource(value):
    from .resources import Resource
    return isinstance(value, Resource)


def is_queryset(value):
    from .querysets import Queryset
    return isinstance(value, Queryset)


def is_dict(value):
    return isinstance(value, collections.abc.Mapping)


def is_list(value):
    return (isinstance(value, collections.abc.Sequence) and
            not isinstance(value, str))


def is_null(value):
    return value is None


def has_data(value):
    return is_dict(value) and 'data' in value


def has_links(value):
    return is_dict(value) and 'links' in value


def is_resource_identifier(value):
    return is_dict(value) and {'type', 'id'} <= set(value.keys())


def is_relationship(value):
    return (is_dict(value) and
            has_data('value') and
            is_dict(value['data']) and
            is_resource_identifier(value['data']))


def is_related(value):
    """ Determines if value can be considered a relationship in any way. """

    return (is_resource(value) or
            is_resource_identifier(value) or
            is_relationship(value))


def is_related_list(value):
    if has_data(value):
        value = value['data']

    return is_list(value) and all((is_related(item) for item in value))
