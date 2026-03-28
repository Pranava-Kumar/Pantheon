"""
Token storage utilities for managing Upstox and other API tokens.
Provides centralized token loading to avoid duplication across the codebase.
"""

from datetime import datetime, timezone
from sqlmodel import select
from pantheon.db.session import SessionLocal
from pantheon.db.models import TokenRecord
from loguru import logger


def get_active_token(provider: str = "upstox") -> TokenRecord | None:
    """
    Load the active token record for a given provider from the database.
    
    Args:
        provider: The token provider (e.g., "upstox", "finnhub").
        
    Returns:
        TokenRecord: The active token record, or None if not found.
    """
    db = SessionLocal()
    try:
        token_record = db.query(TokenRecord).filter_by(
            provider=provider,
            is_active=True
        ).first()
        return token_record
    finally:
        db.close()


def get_active_upstox_token() -> str:
    """
    Load the active Upstox access token from the database.
    
    Returns:
        str: The active Upstox access token.
        
    Raises:
        RuntimeError: If no active Upstox token is found.
    """
    token_record = get_active_token("upstox")
    if not token_record:
        raise RuntimeError("No active Upstox token found. Please authenticate first.")
    return token_record.access_token


def save_token(provider: str, access_token: str, refresh_token: str | None = None,
               expires_at: str | None = None, metadata: dict | None = None) -> TokenRecord:
    """
    Save or update a token record in the database.
    
    Args:
        provider: The token provider name.
        access_token: The access token string.
        refresh_token: Optional refresh token.
        expires_at: Optional expiration timestamp.
        metadata: Optional metadata dictionary.
        
    Returns:
        TokenRecord: The saved token record.
    """
    db = SessionLocal()
    try:
        # Deactivate any existing tokens for this provider
        existing = db.query(TokenRecord).filter_by(provider=provider).all()
        for record in existing:
            record.is_active = False
        
        # Create new token record
        token_record = TokenRecord(
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.fromisoformat(expires_at) if expires_at else None,
            metadata_json=metadata or {},
            is_active=True
        )
        db.add(token_record)
        db.commit()
        db.refresh(token_record)
        logger.info(f"Saved new {provider} token")
        return token_record
    finally:
        db.close()
