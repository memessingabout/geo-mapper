# pbf_to_mbtiles.py  (replace your file)

import subprocess
from pathlib import Path
import shutil

# Directories
TILES_DIR = Path(__file__).parent / "tiles"
PBF_DIR = Path(__file__).parent / "pbf"
TILES_DIR.mkdir(exist_ok=True)
PBF_DIR.mkdir(exist_ok=True)

# Tilemaker config (bundled with release)
CONFIG_JSON = Path("/usr/local/share/tilemaker/config-openmaptiles.json")
PROCESS_LUA = Path("/usr/local/share/tilemaker/process-openmaptiles.lua")

# Fallback: copy from tilemaker binary dir
if not CONFIG_JSON.exists():
    tilemaker_dir = shutil.which("tilemaker")
    if tilemaker_dir:
        base_dir = Path(tilemaker_dir).parent.parent / "share" / "tilemaker"
        CONFIG_JSON = base_dir / "config-openmaptiles.json"
        PROCESS_LUA = base_dir / "process-openmaptiles.lua"

def generate_mbtiles(pbf_path: Path):
    """Convert .osm.pbf → .mbtiles using tilemaker (correct CLI)"""
    if not pbf_path.exists():
        print(f"PBF file not found: {pbf_path}")
        return None

    output = TILES_DIR / f"{pbf_path.stem}.mbtiles"
    if output.exists():
        print(f"Already exists: {output.name}")
        return str(output)

    print(f"Generating {output.name} from {pbf_path.name}...")

    # CORRECT CLI: input output --config --process
    cmd = [
        "tilemaker",
        str(pbf_path),      # ← positional input
        str(output),        # ← positional output
        "--config", str(CONFIG_JSON),
        "--process", str(PROCESS_LUA),
        "--verbose"
    ]

    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Generation complete!")
        print(result.stdout)
        return str(output)
    except subprocess.CalledProcessError as e:
        print("Error during generation:")
        print(e.stderr)
        return None
    except FileNotFoundError:
        print("tilemaker not found. Install it first.")
        return None

def auto_convert():
    """Auto-convert all .osm.pbf in pbf/ folder"""
    pbf_files = list(PBF_DIR.glob("*.osm.pbf"))
    if not pbf_files:
        print("No .osm.pbf files in pbf/ folder. Place your file there.")
        return

    for pbf in pbf_files:
        generate_mbtiles(pbf)

# Run on import
auto_convert()