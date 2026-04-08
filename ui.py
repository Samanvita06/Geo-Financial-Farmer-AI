# ui.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

st.set_page_config(page_title="AgriMineral Pipeline", layout="wide")

st.title("AgriMineral Land Analyzer")
st.caption("Dev 1 — Data Collection + Geo-Spatial Analysis")

# ── Step 1: City Search ──────────────────────────────────────────
st.subheader("Step 1 — Search a city")

col1, col2 = st.columns([4, 1])
with col1:
    city = st.text_input("City name", placeholder="e.g. Bangalore, Mumbai, Delhi...")
with col2:
    st.button("Search")

lat, lon = 20.5937, 78.9629
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
            st.success(f"Found: {data[0]['display_name'].split(',')[0]}")
        else:
            st.error("City not found. Try a different name.")
    except Exception as e:
        st.error(f"Error: {e}")

# ── Step 2: Map ──────────────────────────────────────────────────
st.subheader("Step 2 — Select land region")
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

map_output = st_folium(m, width=None, height=500, returned_objects=["last_active_drawing"])

# ── Step 3: Selection Info ───────────────────────────────────────
bounds = None
selected = map_output.get("last_active_drawing")

if selected:
    coords = selected["geometry"]["coordinates"][0]
    lats = [c[1] for c in coords]
    lons = [c[0] for c in coords]
    north, south = max(lats), min(lats)
    east, west   = max(lons), min(lons)
    clat = round((north + south) / 2, 5)
    clon = round((east + west) / 2, 5)
    dlat = abs(north - south) * 111
    dlon = abs(east - west) * 111 * math.cos(math.radians(clat))
    area = round(dlat * dlon, 2)

    bounds = {
        "center": {"lat": clat, "lon": clon},
        "bounds": {
            "north": round(north, 5),
            "south": round(south, 5),
            "east":  round(east, 5),
            "west":  round(west, 5)
        },
        "area_km2": area
    }

    st.subheader("Step 3 — Selected region")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Center lat", clat)
    c2.metric("Center lon", clon)
    c3.metric("Area", f"{area} km²")
    c4.metric("City", city or "—")

    # ── Step 4: Analyze Button ───────────────────────────────────
    st.subheader("Step 4 — Run agents")
    if st.button("Analyze this land", type="primary", use_container_width=True):
        with st.spinner("Running Agent 1 — collecting data..."):
            try:
                res = requests.post(
                    "http://127.0.0.1:5000/analyze",
                    json={"city": city, "bounds": bounds},
                    timeout=30
                )
                result = res.json()

                if "error" in result:
                    st.error(result["error"])

                else:
                    a1 = result.get("agent1", {})
                    a2 = result.get("agent2", {})

                    # ── Agent 1 Results ──────────────────────────
                    st.markdown("---")
                    st.subheader("Agent 1 — Raw Data")

                    w = a1.get("weather", {}).get("current", {})
                    t = a1.get("terrain", {})

                    r1, r2, r3, r4 = st.columns(4)
                    r1.metric("Temperature",  f"{w.get('temperature_2m', '—')} °C")
                    r2.metric("Humidity",     f"{w.get('relative_humidity_2m', '—')} %")
                    r3.metric("Wind speed",   f"{w.get('windspeed_10m', '—')} km/h")
                    r4.metric("Precipitation",f"{w.get('precipitation', '—')} mm")

                    r5, r6, r7, r8 = st.columns(4)
                    r5.metric("Elevation",    f"{t.get('elevation_m', '—')} m")
                    r6.metric("Terrain",       t.get("terrain_note", "—"))
                    r7.metric("Timezone",      a1.get("weather", {}).get("timezone", "—"))
                    r8.metric("Area selected", f"{area} km²")

                    # Weekly forecast
                    forecast = a1.get("weather", {}).get("weekly_forecast", {})
                    if forecast:
                        st.markdown("**7-day forecast**")
                        days = forecast.get("time", [])
                        tmax = forecast.get("temperature_2m_max", [])
                        tmin = forecast.get("temperature_2m_min", [])
                        rain = forecast.get("precipitation_sum", [])

                        cols = st.columns(len(days)) if days else []
                        for i, col in enumerate(cols):
                            day = days[i].split("-")[-1] if i < len(days) else "—"
                            hi  = tmax[i] if i < len(tmax) else "—"
                            lo  = tmin[i] if i < len(tmin) else "—"
                            rn  = rain[i] if i < len(rain) else "—"
                            col.markdown(
                                f"<div style='text-align:center;font-size:12px;'>"
                                f"<b>{day}</b><br>{hi}°/{lo}°<br>{rn}mm</div>",
                                unsafe_allow_html=True
                            )

                    # Map links
                    maps = a1.get("maps", {})
                    if maps:
                        st.markdown("**Map links**")
                        ml1, ml2, ml3 = st.columns(3)
                        ml1.link_button("OpenStreetMap", maps.get("openstreetmap", "#"), use_container_width=True)
                        ml2.link_button("Google Maps",   maps.get("google_maps", "#"),   use_container_width=True)
                        ml3.link_button("Satellite view",maps.get("satellite_view", "#"),use_container_width=True)

                    # ── Agent 2 Results ──────────────────────────
                    st.markdown("---")
                    st.subheader("Agent 2 — Geo-Spatial Analysis")

                    a2c1, a2c2, a2c3, a2c4 = st.columns(4)
                    a2c1.metric("Climate zone",    a2.get("climate_zone", "—"))
                    a2c2.metric("Land type",       a2.get("land_type", "—"))
                    a2c3.metric("Season",          a2.get("current_season", "—"))
                    a2c4.metric("Mineral hint",    a2.get("mineral_hint", "—").split("—")[0])

                    st.info(f"Soil: {a2.get('soil_hint', '—')}")

                    # Farming vs Mineral scores
                    st.markdown("**Suitability scores**")
                    sc1, sc2 = st.columns(2)

                    farming_score = a2.get("farming_score", 0)
                    mineral_score = a2.get("mineral_score", 0)

                    with sc1:
                        st.metric("Farming score", f"{farming_score} / 10")
                        st.progress(farming_score / 10)

                    with sc2:
                        st.metric("Mineral score", f"{mineral_score} / 10")
                        st.progress(mineral_score / 10)

                    # Verdict
                    st.markdown("---")
                    if farming_score > mineral_score:
                        st.success(f"Verdict: This land is better suited for FARMING (score {farming_score} vs {mineral_score})")
                    elif mineral_score > farming_score:
                        st.warning(f"Verdict: This land has stronger MINERAL potential (score {mineral_score} vs {farming_score})")
                    else:
                        st.info("Verdict: Land is equally suitable for farming and mineral use — deeper analysis needed")

                    # Full JSON for teammates
                    st.markdown("---")
                    with st.expander("Full JSON output — share with Dev 2, 3, 4"):
                        st.json(result)

                    # Save to session
                    st.session_state["agent1_output"] = a1
                    st.session_state["agent2_output"] = a2
                    st.success("Agents 1 + 2 complete. Data ready for Dev 2.")

            except requests.exceptions.ConnectionError:
                st.error("Cannot reach Flask server. Make sure `python app.py` is running in another terminal.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")