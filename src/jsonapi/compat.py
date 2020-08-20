from __future__ import unicode_literals, absolute_import

import json

try:
    JSONDecodeError = json.JSONDecodeError
except AttributeError:
    JSONDecodeError = ValueError

try:
    import collections.abc as abc
except ImportError:
    import collections as abc  # noqa
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs  # noqa
