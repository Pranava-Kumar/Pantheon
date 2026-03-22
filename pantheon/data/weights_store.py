import json
import os
from loguru import logger

WEIGHTS_FILE = "weights.json"

DEFAULT_WEIGHTS = {
    "gemini_pro": 0.25,
    "gemini_flash": 0.20,
    "groq_qwen": 0.20,
    "groq_llama": 0.20,
    "groq_gpt": 0.15
}

def load_weights() -> dict:
    if not os.path.exists(WEIGHTS_FILE):
        return DEFAULT_WEIGHTS
    try:
        with open(WEIGHTS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load weights: {e}")
        return DEFAULT_WEIGHTS

def save_weights(weights: dict) -> None:
    try:
        with open(WEIGHTS_FILE, "w") as f:
            json.dump(weights, f, indent=2)
        logger.info("Weights saved")
    except Exception as e:
        logger.error(f"Failed to save weights: {e}")
