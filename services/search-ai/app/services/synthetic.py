import json
from pathlib import Path

SYNTHETIC_PACKAGES_PATH = Path(__file__).resolve().parents[1] / "data" / "synthetic_packages.json"


def load_synthetic_packages() -> list[dict]:
    if not SYNTHETIC_PACKAGES_PATH.exists():
        return []
    return json.loads(SYNTHETIC_PACKAGES_PATH.read_text(encoding="utf-8"))
