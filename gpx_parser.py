# gpx_parser.py
import gpxpy
from datetime import datetime
from utils import haversine
import pytz

# Timezones
EAT = pytz.timezone('Africa/Nairobi')
UTC = pytz.UTC  # Keep reference


def to_eat(gpx_time):
    """
    Convert any GPX time → EAT (Kenya local time)
    Handles:
    - '2025-11-12T02:03:09z' → treat as EAT
    - '2025-11-12T02:03:09' → treat as EAT
    - Real UTC aware time → convert to EAT
    """
    if gpx_time is None:
        return None

    # 1. Convert to string to check for 'z'
    time_str = gpx_time.isoformat() if hasattr(gpx_time, 'isoformat') else str(gpx_time)

    # 2. CASE: 'z', 'Z', or naive → assume EAT
    if time_str.endswith(('z', 'Z')) or gpx_time.tzinfo is None:
        # Strip 'z'
        clean_str = time_str.removesuffix('z').removesuffix('Z')
        try:
            naive_dt = datetime.fromisoformat(clean_str)
        except:
            naive_dt = gpx_time.replace(tzinfo=None)
        return EAT.localize(naive_dt)

    # 3. CASE: Aware time → check if UTC
    try:
        # Safe way: check if UTC offset is 0
        if gpx_time.utcoffset().total_seconds() == 0:
            return gpx_time.astimezone(EAT)
    except:
        pass  # Fall through

    # 4. Any other timezone → convert
    return gpx_time.astimezone(EAT)


def safe_date_from_filename(name: str) -> str | None:
    try:
        d = name.split('_', 1)[0]
        datetime.strptime(d, '%Y-%m-%d')
        return d
    except:
        return None


def enrich_track(track):
    points = []
    prev = None
    for seg in track.segments:
        for p in seg.points:
            cur = (p.latitude, p.longitude)
            speed = None
            duration = None

            # Use to_eat for display
            display_time = to_eat(p.time)
            calc_time = p.time  # Raw for duration math

            if prev and p.time and prev["calc_time"]:
                dt = (p.time - prev["calc_time"]).total_seconds()
                if dt > 0:
                    dist = haversine(prev["coord"], cur)
                    speed = dist / dt
                    duration = dt

            points.append({
                "coord": cur,
                "time": display_time,      # ← EAT for popup
                "calc_time": calc_time,    # ← raw for math
                "elev": p.elevation,
                "speed": speed,
                "duration": duration
            })
            prev = points[-1]
    return points


def parse_gpx_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return gpxpy.parse(f)
    except Exception as e:
        raise ValueError(f"Failed to parse {path.name}: {e}")