import urllib.request
from pathlib import Path
import sqlite3
from tqdm import tqdm

TILES_DIR = Path(__file__).parent / "tiles"
TILES_DIR.mkdir(exist_ok=True)

# Kenya MBTiles (zoom 0–14, ~180 MB) – OpenMapTiles
KENYA_URL = "https://data.openmaptiles.org/planet/africa/kenya.mbtiles"
KENYA_FILE = TILES_DIR / "kenya.mbtiles"

def download_with_progress(url, dest):
    """Download with progress bar"""
    print(f"Downloading {url.split('/')[-1]}...")
    with urllib.request.urlopen(url) as response, open(dest, 'wb') as out_file:
        total = int(response.headers.get('Content-Length', 0))
        with tqdm(total=total, unit='B', unit_scale=True, desc=dest.name) as pbar:
            for chunk in iter(lambda: response.read(1024*1024), b''):
                out_file.write(chunk)
                pbar.update(len(chunk))
    print("Download complete.")

def is_valid_mbtiles(path):
    """Check if file is a valid MBTiles database"""
    if not path.exists() or path.stat().st_size < 1000:
        return False
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='metadata';")
        conn.close()
        return True
    except:
        return False

def ensure_kenya_tiles():
    """Download Kenya tiles if missing or corrupt"""
    if KENYA_FILE.exists() and is_valid_mbtiles(KENYA_FILE):
        print(f"Kenya tiles ready: {KENYA_FILE.name}")
        return str(KENYA_FILE)

    print("No valid Kenya tiles found. Downloading...")
    try:
        download_with_progress(KENYA_URL, KENYA_FILE)
        if is_valid_mbtiles(KENYA_FILE):
            print("Kenya tiles ready for offline use!")
            return str(KENYA_FILE)
        else:
            KENYA_FILE.unlink(missing_ok=True)
            raise ValueError("Downloaded file is not valid MBTiles")
    except Exception as e:
        print(f"Failed to download tiles: {e}")
        return None

# Run on import
ensure_kenya_tiles()
