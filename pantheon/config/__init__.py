import yaml
import os

def load_watchlist() -> list[dict]:
    path = os.path.join(os.path.dirname(__file__), "watchlist.yaml")
    with open(path, "r") as f:
        return yaml.safe_load(f)
