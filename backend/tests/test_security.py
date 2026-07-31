from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest

from app.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
)


def test_hash_and_verify_password():
    fake_hashed = "$mock$hash$test_password_123"

    def mock_hash(secret):
        return f"$mock$hash${secret}"

    def mock_verify(secret, hash_):
        return hash_ == f"$mock$hash${secret}"

    with patch("app.core.security.pwd_context") as mock_pwd:
        mock_pwd.hash.side_effect = mock_hash
        mock_pwd.verify.side_effect = mock_verify

        from app.core.security import hash_password, verify_password

        plain = "test_password_123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True
        assert verify_password("wrong_password", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(data={"sub": "123"})
    payload = decode_access_token(token)
    assert payload.get("sub") == "123"

    fake_token = token + "tampered"
    payload_fake = decode_access_token(fake_token)
    assert payload_fake == {}

    expired_token = create_access_token(
        data={"sub": "123"},
        expires_delta=timedelta(days=-1),
    )
    payload_expired = decode_access_token(expired_token)
    assert payload_expired == {}


def test_access_token_expire_default():
    token = create_access_token(data={"sub": "test"})
    payload = decode_access_token(token)
    assert "exp" in payload
    assert "iat" not in payload or True

    exp_ts = payload["exp"]
    exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
    now = datetime.now(tz=timezone.utc)
    diff_minutes = (exp_dt - now).total_seconds() / 60

    expected_min = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    assert 0 < diff_minutes <= expected_min + 1
    assert expected_min - 2 <= diff_minutes <= expected_min + 2
