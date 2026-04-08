# ui.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json

st.set_page_config(page_title="AgriMineral Pipeline", layout="wide")

st.title("AgriMineral Land Analyzer")
st.caption("Dev 1 — Data Collection Agent")

# ── Step 1: City Search ──────────────────────────────────────────
st.subheader("Step 1 — Search a city")

col1, col2 = st.columns([4, 1])
with col1:
    city = st.text_input("City name", placeholder="e.g. Bangalore, Mumbai, Delhi...")
with col2:
    search = st.button("Search", use_container_width=True)

lat, lon = 20.5937, 78.9629  # default: center of India
city_found = False

if city:
    try:
        res = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "AgriMineralPipeline/1.0"}
        )
        data = res.json()
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            city_found = True
            st.success(f"Found: {data[0]['display_name'].split(',')[0]}, {data[0]['display_name'].split(',')[-1]}")
        else:
            st.error("City not found. Try a different name.")
    except Exception as e:
        st.error(f"Error: {e}")

# ── Step 2: Map + Draw Region ────────────────────────────────────
st.subheader("Step 2 — Select land region on map")
st.caption("Draw a rectangle on the map to select your land area")

m = folium.Map(location=[lat, lon], zoom_start=12 if city_found else 5)
folium.plugins.Draw(
    export=False,
    draw_options={
        "rectangle": True,
        "polygon": False,
        "circle": False,
        "marker": False,
        "polyline": False,
        "circlemarker": False,
    },
    edit_options={"edit": False}
).add_to(m)

map_output = st_folium(m, width=None, height=480, returned_objects=["last_active_drawing"])

# ── Step 3: Extract Coords + Run Agent ──────────────────────────
bounds = None
selected = map_output.get("last_active_drawing")

if selected:
    coords = selected["geometry"]["coordinates"][0]
    lats = [c[1] for c in coords]
    lons = [c[0] for c in coords]
    north, south = max(lats), min(lats)
    east, west = max(lons), min(lons)
    clat = round((north + south) / 2, 5)
    clon = round((east + west) / 2, 5)

    import math
    dlat = abs(north - south) * 111
    dlon = abs(east - west) * 111 * math.cos(math.radians(clat))
    area = round(dlat * dlon, 2)

    bounds = {
        "center": {"lat": clat, "lon": clon},
        "bounds": {
            "north": round(north, 5),
            "south": round(south, 5),
            "east": round(east, 5),
            "west": round(west, 5)
        },
        "area_km2": area
    }

    st.subheader("Step 3 — Selected region")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Center lat", clat)
    c2.metric("Center lon", clon)
    c3.metric("Area", f"{area} km²")
    c4.metric("City", city or "—")

    st.subheader("Step 4 — Analyze")
    if st.button("Analyze this land", type="primary", use_container_width=True):
        with st.spinner("Agent 1 collecting data..."):
            try:
                res = requests.post(
                    "http://127.0.0.1:5000/analyze",
                    json={"city": city, "bounds": bounds}
                )
                result = res.json()

                if "error" in result:
                    st.error(result["error"])
                else:
                    st.subheader("Results")

                    # Weather
                    st.markdown("**Weather**")
                    w = result.get("weather", {}).get("current", {})
                    wc1, wc2, wc3, wc4 = st.columns(4)
                    wc1.metric("Temperature", f"{w.get('temperature_2m', '—')} °C")
                    wc2.metric("Humidity", f"{w.get('relative_humidity_2m', '—')} %")
                    wc3.metric("Wind speed", f"{w.get('windspeed_10m', '—')} km/h")
                    wc4.metric("Precipitation", f"{w.get('precipitation', '—')} mm")

                    # Terrain
                    st.markdown("**Terrain**")
                    t = result.get("terrain", {})
                    tc1, tc2 = st.columns(2)
                    tc1.metric("Elevation", f"{t.get('elevation_m', '—')} m")
                    tc2.metric("Terrain type", t.get("terrain_note", "—"))

                    # Map links
                    st.markdown("**Map links**")
                    maps = result.get("maps", {})
                    ml1, ml2, ml3 = st.columns(3)
                    ml1.link_button("OpenStreetMap", maps.get("openstreetmap", "#"))
                    ml2.link_button("Google Maps", maps.get("google_maps", "#"))
                    ml3.link_button("Satellite view", maps.get("satellite_view", "#"))

                    # Full JSON for Dev 2
                    with st.expander("Full JSON output (for Dev 2)"):
                        st.json(result)

                    # Save to session for Dev 2 handoff
                    st.session_state["agent1_output"] = result
                    st.success("Agent 1 complete. Data ready for Dev 2.")

            except Exception as e:
                st.error(f"Cannot reach Flask server. Make sure `python app.py` is running.\n\n{e}")