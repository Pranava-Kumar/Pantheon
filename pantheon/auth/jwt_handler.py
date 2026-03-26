from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from pantheon.config.settings import settings

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a JWT access token.
    
    Args:
        data (dict): The data to encode in the token.
        expires_delta (Optional[timedelta]): The expiration time delta.
    
    Returns:
        str: The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT access token.
    
    Args:
        token (str): The token to decode.
    
    Returns:
        dict: The decoded token payload.
    
    Raises:
        jwt.ExpiredSignatureError: If the token is expired.
        jwt.InvalidTokenError: If the token is invalid.
    """
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
