import datetime


class BearerAuthentication:
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self):
        return {'Authorization': f"Bearer {self.api_key}"}


class ULFAuthentication:
    def __init__(self, public, secret=None):
        self.public = public
        self.secret = secret

    def __call__(self):
        if self.secret is None:
            return {'Authorization': f"ULF {self.public}"}
        else:
            return {'Authorization': f"ULF {self.public}:{self.secret}"}


class JWTAuthentication:
    """
        Usage:

            >>> from jsonapi import setup
            >>> setup(host="https://some.host.com",
            ...       auth=JWTAuthentication(payload={'username': "username"},
            ...                               secret="SHARED_SECRET",
            ...                               duration=300))
    """

    def __init__(self, payload, secret, duration, algorithm="HS256",
                 get_now=None):
        self.payload = dict(payload)
        self.secret = secret
        self.duration = duration
        self.algorithm = algorithm

        # Dependency injection for getting the current timestamp; maybe it will
        # make testing easier
        if get_now is None:
            get_now = datetime.datetime.utcnow
        self.get_now = get_now

    def __call__(self):
        import jwt  # Optional requirement, don't require at top level

        exp = self.get_now() + datetime.timedelta(seconds=self.duration)
        payload = dict(self.payload)
        payload['exp'] = exp
        token = jwt.encode(payload=payload,
                           secret=self.secret,
                           algorithm=self.algorithm)
        return {'Authorization': f"JWT {token}"}
