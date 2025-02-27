import trino
from requests.auth import AuthBase
from requests import PreparedRequest, Session
from trino.auth import Authentication

class _CustomAuth(AuthBase):
    def __init__(self, token: str):
        self.token = token.replace("Bearer ", "", 1)

    def __call__(self, r: PreparedRequest) -> PreparedRequest:
        r.headers["access_token"] = self.token
        return r

class CustomJWTAuthentication(Authentication):
    def __init__(self, token: str):
        self.token = token

    def set_http_session(self, http_session: Session) -> Session:
        http_session.auth = _CustomAuth(self.token)
        return http_session