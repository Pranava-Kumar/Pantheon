import pytest
from pantheon.auth.utils import get_password_hash, verify_password

def test_password_hashing():
    password = "secret-password"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)

def test_password_different_hashes():
    password = "secret-password"
    hashed1 = get_password_hash(password)
    hashed2 = get_password_hash(password)
    # bcrypt should use different salts
    assert hashed1 != hashed2
