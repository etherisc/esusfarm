import jwt
import pytest
from fastapi import HTTPException

from server.auth import verify_access_token
from server.config import settings


def test_verify_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(settings, "API_JWT_SECRET", "test-secret")
    token = jwt.encode({"sub": "esusfarm-test"}, "test-secret", algorithm="HS256")
    verify_access_token(token)


def test_verify_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "API_JWT_SECRET", "test-secret")
    with pytest.raises(HTTPException) as exc:
        verify_access_token("not-a-jwt")
    assert exc.value.status_code == 401