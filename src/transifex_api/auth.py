class BearerAuthentication:
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self):
        return f"Bearer {self.api_key}"


class ULFAuthentication:
    def __init__(self, public, secret=None):
        self.public = public
        self.secret = secret

    def __call__(self):
        if self.secret is None:
            return f"ULF {self.public}"
        else:
            return f"ULF {self.public}:{self.secret}"
