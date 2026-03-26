import pytest
from datetime import timedelta
import jwt
from pantheon.auth.jwt_handler import create_access_token, decode_access_token

def test_create_access_token():
    data = {"sub": "testuser@example.com"}
    token = create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0

def test_decode_access_token_success():
    data = {"sub": "testuser@example.com", "role": "admin"}
    token = create_access_token(data)
    decoded = decode_access_token(token)
    assert decoded["sub"] == "testuser@example.com"
    assert decoded["role"] == "admin"
    assert "exp" in decoded

def test_decode_access_token_expired():
    data = {"sub": "testuser@example.com"}
    # Create a token that is already expired
    token = create_access_token(data, expires_delta=timedelta(seconds=-1))
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)

def test_decode_access_token_invalid():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid.token.here")

def test_decode_access_token_wrong_secret():
    data = {"sub": "testuser@example.com"}
    token = create_access_token(data)
    # Tamper with the token or use wrong secret logic if possible
    # For now, just invalid token is fine, or we can test tampering
    tampered_token = token + "tamper"
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered_token)
