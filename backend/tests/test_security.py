"""Unit tests for password hashing and JWT helpers (app/utils/security.py)."""
from datetime import datetime, timedelta
from uuid import uuid4

from jose import jwt

from app.config import settings
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("s3cret-pass")
        assert hashed != "s3cret-pass"
        assert hashed.startswith("$2")  # bcrypt prefix

    def test_verify_correct_password(self):
        hashed = hash_password("s3cret-pass")
        assert verify_password("s3cret-pass", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("s3cret-pass")
        assert verify_password("wrong-pass", hashed) is False

    def test_hash_is_salted_each_call(self):
        # bcrypt uses a random salt, so two hashes of the same input differ.
        assert hash_password("same") != hash_password("same")


class TestJwt:
    def test_roundtrip_returns_same_uuid(self):
        user_id = uuid4()
        token = create_access_token(user_id)
        assert decode_access_token(token) == user_id

    def test_garbage_token_returns_none(self):
        assert decode_access_token("not-a-real-token") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token(uuid4())
        tampered = token[:-3] + ("abc" if not token.endswith("abc") else "xyz")
        assert decode_access_token(tampered) is None

    def test_expired_token_returns_none(self):
        # Forge a token that expired an hour ago.
        payload = {
            "sub": str(uuid4()),
            "exp": datetime.utcnow() - timedelta(hours=1),
        }
        expired = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        assert decode_access_token(expired) is None

    def test_token_missing_sub_returns_none(self):
        payload = {"exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        assert decode_access_token(token) is None
