"""decode_jwt/jwt_is_valid — no signature verification (waipu's own
server does that), just base64url payload extraction."""
import base64
import json
import time

from .helpers import api


def _make_token(payload: dict) -> str:
    """Build a syntactically-real JWT (unsigned) for testing."""
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"header.{body}.signature"


class TestDecodeJwt:
    def test_decodes_payload(self):
        payload = {"sub": "user-1", "exp": 9999999999}
        assert api.decode_jwt(_make_token(payload)) == payload

    def test_handles_url_safe_characters(self):
        # A payload whose base64 contains '-'/'_' (url-safe alphabet) —
        # decode_jwt must translate those back to '+'/'/' before decoding.
        payload = {"data": "\xff\xfe\xfd" * 10}
        assert api.decode_jwt(_make_token(payload)) == payload

    def test_malformed_raises(self):
        try:
            api.decode_jwt("not-a-jwt")
            assert False, "expected WaipuError"
        except api.WaipuError:
            pass


class TestJwtIsValid:
    def test_none_is_invalid(self):
        assert api.jwt_is_valid(None) is False

    def test_expired_is_invalid(self):
        token = _make_token({"exp": time.time() - 3600})
        assert api.jwt_is_valid(token) is False

    def test_future_exp_is_valid(self):
        token = _make_token({"exp": time.time() + 3600})
        assert api.jwt_is_valid(token) is True

    def test_threshold_treats_near_expiry_as_invalid(self):
        token = _make_token({"exp": time.time() + 30})
        assert api.jwt_is_valid(token, threshold_sec=60) is False
        assert api.jwt_is_valid(token, threshold_sec=0) is True

    def test_malformed_token_is_invalid_not_raising(self):
        assert api.jwt_is_valid("garbage") is False

    def test_missing_exp_treated_as_expired(self):
        token = _make_token({"sub": "user-1"})
        assert api.jwt_is_valid(token) is False
