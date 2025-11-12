# map_generator.py
import folium
from folium.plugins import AntPath, MiniMap
from tkinter import messagebox
from config import MAPS_DIR
from utils import speed_to_color, haversine
from gpx_parser import enrich_track, to_eat

def create_map(gpx, date_str: str, output_path, map_dark_mode: bool, use_offline):
    all_coords = []
    track_segments = []
    total_dist = 0
    total_duration = 0
    stop_duration = 0

    for track in gpx.tracks:
        enriched = enrich_track(track)
        if len(enriched) < 2: continue
        coords = [p["coord"] for p in enriched]
        all_coords.extend(coords)
        track_segments.append((coords, enriched))

        # Calculate distance & duration
        for i in range(1, len(enriched)):
            total_dist += haversine(enriched[i-1]["coord"], enriched[i]["coord"])
            if enriched[i]["duration"]:
                total_duration += enriched[i]["duration"]

    if not all_coords:
        return False, "No track data"

    # Waypoints = stops
    waypoints = sorted(gpx.waypoints, key=lambda wp: to_eat(wp.time) if wp.time else None)
    for i in range(1, len(waypoints)):
        if waypoints[i].time and waypoints[i-1].time:
            delta = (to_eat(waypoints[i].time) - to_eat(waypoints[i-1].time)).total_seconds()
            if delta > 60:  # Only count stops > 1 min
                stop_duration += delta

    lats, lons = zip(*all_coords)
    center = [sum(lats)/len(lats), sum(lons)/len(lons)]

    # DARK TILES
    tile = 'cartodbdark_matter' if map_dark_mode else 'cartodbpositron'
    m = folium.Map(location=center, zoom_start=13, tiles=tile)

    if use_offline:
        folium.TileLayer(
            tiles=f'file://{use_offline}',
            attr='Offline MBTiles',
            name='Offline',
            overlay=False
        ).add_to(m)

    m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])

    # Animation + Speed
    for coords, _ in track_segments:
        AntPath(coords, color="#ff00ff", weight=4, opacity=0.8, delay=1000).add_to(m)

    for coords, enriched in track_segments:
        for i in range(len(coords) - 1):
            seg = [coords[i], coords[i+1]]
            folium.PolyLine(seg, color=speed_to_color(enriched[i+1]["speed"]), weight=3).add_to(m)

    # Start/Finish
    if track_segments:
        first = track_segments[0][1][0]
        last = track_segments[-1][1][-1]
        folium.Marker(first["coord"], popup=folium.Popup(f"<b>START</b><br>Time: {first['time'].strftime('%H:%M') if first['time'] else '—'}", max_width=200),
                      icon=folium.Icon(color="green", icon="play", prefix='fa')).add_to(m)
        folium.Marker(last["coord"], popup=folium.Popup(f"<b>FINISH</b><br>Time: {last['time'].strftime('%H:%M') if last['time'] else '—'}", max_width=200),
                      icon=folium.Icon(color="darkred", icon="stop", prefix='fa')).add_to(m)

    # Waypoints
    for wp in gpx.waypoints:
        t = to_eat(wp.time)
        time_str = t.strftime('%H:%M') if t else '—'
        folium.CircleMarker([wp.latitude, wp.longitude], radius=7, color="purple", fill=True,
                            popup=folium.Popup(f"<b>{wp.name or 'Stop'}</b><br>Time: {time_str}", max_width=250)).add_to(m)

    MiniMap().add_to(m)

    # Legend
    legend_html = '''
    <div id="legend-container" style="position:fixed;bottom:60px;left:20px;z-index:1000;">
        <button id="legend-toggle" onclick="toggleLegend()" style="background:#333;color:white;padding:8px 12px;border:none;border-radius:6px;cursor:pointer;">Show Legend</button>
        <div id="speed-legend" style="display:none;margin-top:5px;background:white;padding:12px;border:2px solid #555;border-radius:8px;font-size:13px;">
            <b>Speed Legend</b><br>
            <div><i style="background:#00ff00;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> less than 5 km/h</div>
            <div><i style="background:#88ff00;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> 5–15 km/h</div>
            <div><i style="background:#ffff00;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> 15–30 km/h</div>
            <div><i style="background:#ff8800;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> 30–50 km/h</div>
            <div><i style="background:#ff0000;width:12px;height:12px;display:inline-block;border-radius:50%;"></i> greater than 50 km/h</div>
        </div>
    </div>
    <script>
    function toggleLegend() {
        var l = document.getElementById('speed-legend');
        var b = document.getElementById('legend-toggle');
        if (l.style.display === 'none') { l.style.display = 'block'; b.innerText = 'Hide Legend'; }
        else { l.style.display = 'none'; b.innerText = 'Show Legend'; }
    }
    </script>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # FOOTER: Stats + Signature
    hours, rem = divmod(total_duration, 3600)
    mins = rem // 60
    stop_pct = (stop_duration / total_duration * 100) if total_duration > 0 else 0

    footer = f'''
    <div style="position:fixed; bottom:0; left:0; width:100%; background:rgba(0,0,0,0.7); color:white; padding:8px; text-align:center; font-family:Arial; font-size:13px; z-index:1000;">
        <b>Total:</b> {hours:02.0f}h {mins:02.0f}m | 
        <b>Distance:</b> {total_dist/1000:.2f} km | 
        <b>Stops:</b> {stop_pct:.1f}% ({stop_duration/60:.0f} min) &nbsp; | &nbsp;
        <small><!-- Living on Love --></small>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(footer))

    if output_path.exists():
        if not messagebox.askyesno("Overwrite?", f"File exists:\n{output_path.name}\nOverwrite?"):
            return False, "Cancelled"

    m.save(str(output_path))
    return True, str(output_path)
