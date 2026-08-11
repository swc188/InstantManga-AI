class FakeResponse:
    def __init__(self, status_code=200, json=None, content=b"", text=""):
        self.status_code = status_code
        self._json = json or {}
        self.content = content
        self.text = text

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected status {self.status_code}")


class FakeClient:
    def __init__(self, handler):
        self.handler = handler

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url, **kw):
        return self.handler("GET", url, **kw)

    def post(self, url, **kw):
        return self.handler("POST", url, **kw)
