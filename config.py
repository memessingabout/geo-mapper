# config.py
from pathlib import Path
import json

BASE_DIR = Path(__file__).parent
MAPS_DIR = BASE_DIR / "maps"
TILES_DIR = BASE_DIR / "tiles"
SETTINGS_FILE = BASE_DIR / "settings.json"

MAPS_DIR.mkdir(exist_ok=True)
TILES_DIR.mkdir(exist_ok=True)

DEFAULT_TILES = next(TILES_DIR.glob("*.mbtiles"), None)

def load_settings():
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARN] Failed to load settings: {e}")
    return {
        "last_folder": "",
        "dark_mode": False,
        "show_legend": True,
        "offline_tiles": str(DEFAULT_TILES) if DEFAULT_TILES else ""
    }

def save_settings(data):
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to save settings: {e}")
