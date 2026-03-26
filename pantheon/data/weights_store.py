"""
Persistent model weight storage using Neon PostgreSQL.

Replaces the previous local weights.json implementation.
GitHub Actions runners have ephemeral filesystems, so weights
must be stored in the database to persist across runs.
"""

from datetime import datetime
from loguru import logger
from sqlmodel import select

from pantheon.db.session import SessionLocal, init_db
from pantheon.db.models import ModelWeight
from pantheon.mmci.weights import load_config_weights

def load_weights() -> dict:
    """Load current model weights from the database.
    Falls back to config weights if table is empty or on error."""
    config_weights = load_config_weights()
    try:
        db = SessionLocal()
        try:
            rows = db.exec(select(ModelWeight)).all()
            if not rows:
                return dict(config_weights)
            return {row.model_id: row.weight for row in rows}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to load weights from DB: {e}")
        return dict(config_weights)


def save_weights(weights: dict) -> None:
    """Upsert model weights into the database."""
    try:
        db = SessionLocal()
        try:
            for model_id, weight in weights.items():
                existing = db.get(ModelWeight, model_id)
                if existing:
                    existing.weight = weight
                    existing.updated_at = datetime.utcnow()
                    db.add(existing)
                else:
                    db.add(ModelWeight(
                        model_id=model_id,
                        weight=weight,
                        updated_at=datetime.utcnow(),
                    ))
            db.commit()
            logger.info("Weights saved to database")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to save weights to DB: {e}")
