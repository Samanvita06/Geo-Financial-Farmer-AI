import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math
import pandas as pd

st.set_page_config(page_title="AgriMineral Pipeline", layout="wide")

st.markdown("""
<style>
.main-title  { font-size:40px; font-weight:700; color:#2E7D32; }
.crop-card   { background:linear-gradient(135deg,#e8f5e9,#f1f8e9); border-left:4px solid #2E7D32; padding:12px 16px; border-radius:10px; margin-bottom:10px; font-size:14px; }
.agent-header{ background-color:#2E7D32; color:white; padding:8px 14px; border-radius:8px; font-weight:600; font-size:16px; display:inline-block; margin-bottom:10px; }
.eda-header  { background-color:#1565C0; color:white; padding:8px 14px; border-radius:8px; font-weight:600; font-size:16px; display:inline-block; margin-bottom:10px; }
.dash-header { background-color:#4A148C; color:white; padding:8px 14px; border-radius:8px; font-weight:600; font-size:16px; display:inline-block; margin-bottom:10px; }
.action-sell { background:#e8f5e9; border-left:5px solid #2e7d32; padding:10px 14px; border-radius:8px; font-weight:600; font-size:15px; margin-bottom:8px; }
.action-hold { background:#fff8e1; border-left:5px solid #f9a825; padding:10px 14px; border-radius:8px; font-weight:600; font-size:15px; margin-bottom:8px; }
.action-store{ background:#fce4ec; border-left:5px solid #c62828; padding:10px 14px; border-radius:8px; font-weight:600; font-size:15px; margin-bottom:8px; }
.fin-profit  { background:#e8f5e9; border-left:5px solid #2e7d32; padding:14px 18px; border-radius:10px; margin-bottom:10px; }
.fin-loss    { background:#fce4ec; border-left:5px solid #c62828; padding:14px 18px; border-radius:10px; margin-bottom:10px; }
.insight-box { background:#f8f9fa; border-left:4px solid #1565C0; padding:10px 14px; border-radius:8px; margin-bottom:8px; font-size:14px; }
.cross-box   { background:#f3e5f5; border-left:4px solid #7B1FA2; padding:10px 14px; border-radius:8px; margin-bottom:8px; font-size:14px; }
.summary-box { background:linear-gradient(135deg,#1b5e20,#2e7d32); color:white; padding:20px 24px; border-radius:14px; margin-bottom:16px; }
.dash-card   { background:#1e1e1e;color:white; border:1px solid #e0e0e0; border-radius:12px; padding:16px 20px; margin-bottom:12px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🌱 AgriMineral Land Analyzer</div>", unsafe_allow_html=True)
st.caption("AI-powered Geo-Spatial Farming Intelligence")

# ── Step 1 ───────────────────────────────────────────────────────
st.subheader("Step 1 — Search a city or area")
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
            lat = float(data[0]["lat"]); lon = float(data[0]["lon"]); city_found = True
            st.success(f"Found: {data[0]['display_name'].split(',')[0]}")
        else:
            st.error("City not found.")
    except Exception as e:
        st.error(f"Error: {e}")

# ── Step 2 ───────────────────────────────────────────────────────
st.subheader("Step 2 — Select land region")
st.caption("Draw a rectangle on the map to select your land area")
m = folium.Map(location=[lat, lon], zoom_start=12 if city_found else 5)
folium.plugins.Draw(
    export=False,
    draw_options={"rectangle":True,"polygon":False,"circle":False,"marker":False,"polyline":False,"circlemarker":False},
    edit_options={"edit": False}
).add_to(m)
map_output = st_folium(m, width=None, height=500, returned_objects=["last_active_drawing"])

# ── Step 3 ───────────────────────────────────────────────────────
bounds   = None
selected = map_output.get("last_active_drawing")
if selected:
    coords = selected["geometry"]["coordinates"][0]
    lats = [c[1] for c in coords]; lons = [c[0] for c in coords]
    north,south = max(lats),min(lats); east,west = max(lons),min(lons)
    clat = round((north+south)/2,5); clon = round((east+west)/2,5)
    dlat = abs(north-south)*111
    dlon = abs(east-west)*111*math.cos(math.radians(clat))
    area = round(dlat*dlon,2)
    bounds = {
        "center":{"lat":clat,"lon":clon},
        "bounds":{"north":round(north,5),"south":round(south,5),"east":round(east,5),"west":round(west,5)},
        "area_km2": area
    }
    st.subheader("Step 3 — Selected region")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Center lat", clat); c2.metric("Center lon", clon)
    c3.metric("Area", f"{area} km²"); c4.metric("City", city or "—")

    # ── Step 4 ───────────────────────────────────────────────────
    st.subheader("Step 4 — Run Full Agent Pipeline")
    if st.button("Analyze this land", type="primary", use_container_width=True):
        with st.spinner("Running all agents..."):
            try:
                res = requests.post("http://127.0.0.1:5000/analyze",
                                    json={"city":city,"bounds":bounds}, timeout=60)
                result = res.json()

                if "error" in result:
                    st.error(result["error"])
                else:
                    a1  = result.get("agent1", {})
                    a2  = result.get("agent2", {})
                    a3  = result.get("agent3_soil", {})
                    a4  = result.get("agent4_yield", {})
                    a5  = result.get("agent5_marketing", {})
                    a6  = result.get("agent6_financial", {})
                    a7  = result.get("agent7_eda", {})

                    # ── Agent 1 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>🛰️ Agent 1 — Raw Data Collection</div>", unsafe_allow_html=True)
                    w = a1.get("weather",{}).get("current",{}); t = a1.get("terrain",{})
                    r1,r2,r3,r4 = st.columns(4)
                    r1.metric("Temperature",    f"{w.get('temperature_2m','—')} °C")
                    r2.metric("Humidity",        f"{w.get('relative_humidity_2m','—')} %")
                    r3.metric("Wind speed",      f"{w.get('windspeed_10m','—')} km/h")
                    r4.metric("Precipitation",   f"{w.get('precipitation','—')} mm")
                    r5,r6,r7,r8 = st.columns(4)
                    r5.metric("Elevation",       f"{t.get('elevation_m','—')} m")
                    r6.metric("Terrain",         t.get("terrain_note","—"))
                    r7.metric("Timezone",        a1.get("weather",{}).get("timezone","—"))
                    r8.metric("Area selected",   f"{area} km²")
                    forecast = a1.get("weather",{}).get("weekly_forecast",{})
                    if forecast:
                        st.markdown("**7-day forecast**")
                        days=forecast.get("time",[]); tmax=forecast.get("temperature_2m_max",[])
                        tmin=forecast.get("temperature_2m_min",[]); rain=forecast.get("precipitation_sum",[])
                        cols = st.columns(len(days)) if days else []
                        for i,col in enumerate(cols):
                            day = days[i].split("-")[-1] if i<len(days) else "—"
                            col.markdown(f"<div style='text-align:center;font-size:12px;'><b>{day}</b><br>{tmax[i] if i<len(tmax) else '—'}°/{tmin[i] if i<len(tmin) else '—'}°<br>{rain[i] if i<len(rain) else '—'}mm</div>", unsafe_allow_html=True)
                    maps = a1.get("maps",{})
                    if maps:
                        st.markdown("**Map links**")
                        ml1,ml2,ml3 = st.columns(3)
                        ml1.link_button("OpenStreetMap", maps.get("openstreetmap","#"), use_container_width=True)
                        ml2.link_button("Google Maps",   maps.get("google_maps","#"),   use_container_width=True)
                        ml3.link_button("Satellite view",maps.get("satellite_view","#"),use_container_width=True)

                    # ── Agent 2 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>🌍 Agent 2 — Geo-Spatial Analysis</div>", unsafe_allow_html=True)
                    a2c1,a2c2,a2c3 = st.columns(3)
                    a2c1.metric("Climate zone", a2.get("climate_zone","—"))
                    a2c2.metric("Land type",    a2.get("land_type","—"))
                    a2c3.metric("Season",       a2.get("current_season","—"))
                    farming_score = a2.get("farming_score",0); soil_health = a2.get("soil_health_score",0)
                    st.markdown("**Overall scores**")
                    sc1,sc2 = st.columns(2)
                    with sc1: st.metric("Farming suitability",f"{farming_score} / 10"); st.progress(farming_score/10)
                    with sc2: st.metric("Soil health",        f"{soil_health} / 10");   st.progress(soil_health/10)
                    if farming_score>=7:   st.success(f"Highly suitable — {farming_score}/10")
                    elif farming_score>=5: st.warning(f"Moderately suitable — {farming_score}/10")
                    else:                  st.error(f"Needs treatment — {farming_score}/10")

                    # ── Agent 3 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>🧪 Agent 3 — Soil & Crop Recommendation</div>", unsafe_allow_html=True)
                    if a3:
                        sa1,sa2,sa3,sa4 = st.columns(4)
                        sa1.metric("Nitrogen (N)",   f"{a3.get('n','—')} kg/ha")
                        sa2.metric("Phosphorus (P)", f"{a3.get('p','—')} kg/ha")
                        sa3.metric("Potassium (K)",  f"{a3.get('k','—')} kg/ha")
                        sa4.metric("Soil pH",        a3.get("ph","—"))
                        st.metric("Soil type", a3.get("soil_type","—"))
                        recommended_crops = a3.get("recommended_crops",[])
                        if recommended_crops:
                            st.markdown("**🌾 Recommended crops**")
                            crop_cols = st.columns(min(len(recommended_crops),4))
                            for i,crop in enumerate(recommended_crops):
                                with crop_cols[i%4]:
                                    st.markdown(f"<div class='crop-card'>🌿 <b>{crop.capitalize()}</b></div>", unsafe_allow_html=True)
                    else:
                        st.warning("Agent 3 returned no data.")

                    # ── Agent 4 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>📈 Agent 4 — Yield Prediction</div>", unsafe_allow_html=True)
                    if a4 and a4.get("best_crop","—") != "—":
                        y1,y2,y3 = st.columns(3)
                        y1.metric("Best Crop",       a4.get("best_crop","—"))
                        y2.metric("Estimated Yield", a4.get("estimated_yield","—"))
                        y3.metric("Confidence",      f"{a4.get('confidence',0)}%")
                        all_preds = a4.get("all_predictions",{})
                        if all_preds:
                            st.markdown("**All crop yield predictions**")
                            pred_cols = st.columns(min(len(all_preds),4))
                            for i,(crop,val) in enumerate(all_preds.items()):
                                pred_cols[i%4].metric(crop.capitalize(), val)
                    else:
                        st.warning("No yield predictions available.")

                    # ── Agent 5 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>💹 Agent 5 — Marketing Intelligence</div>", unsafe_allow_html=True)
                    if a5 and a5.get("status")=="success":
                        crops_data = a5.get("crops",{}); best_mkt_crop = a5.get("best_market_crop","—")
                        st.info(f"📅 Analysis: **{a5.get('analysis_month','—')} {a5.get('analysis_year','—')}** | 🏆 Best opportunity: **{(best_mkt_crop or '—').capitalize()}**")
                        for crop_name, info in crops_data.items():
                            if info.get("status")=="no_data":
                                st.warning(f"⚠️ {crop_name}: {info.get('message','No data')}"); continue
                            with st.expander(f"📊 {crop_name.capitalize()} — WPI: {info.get('current_wpi','—')} | {info.get('market_action','—')}", expanded=(crop_name==best_mkt_crop)):
                                m1,m2,m3,m4,m5 = st.columns(5)
                                m1.metric("Current WPI",    info.get("current_wpi","—"), delta=f"{info.get('yoy_change_pct',0):+.1f}% YoY")
                                m2.metric("Historical Avg", info.get("historical_avg","—"))
                                m3.metric("Volatility",     f"{info.get('volatility_score','—')} / 10")
                                m4.metric("Best Month",     info.get("best_selling_month","—"))
                                m5.metric("Worst Month",    info.get("worst_selling_month","—"))
                                action = info.get("market_action",""); action_col = info.get("action_color","warning")
                                css_class = "action-sell" if action_col=="success" else "action-store" if action_col=="error" else "action-hold"
                                st.markdown(f"<div class='{css_class}'>Market Action: {action}</div>", unsafe_allow_html=True)
                                for r in info.get("action_reasons",[]): st.markdown(f"- {r}")
                                trend = info.get("trend_12m",[])
                                if trend:
                                    trend_df = pd.DataFrame(trend).set_index("month")
                                    st.markdown("**WPI trend — last 12 months**")
                                    st.line_chart(trend_df, use_container_width=True, height=160)
                        valid_crops = {k:v for k,v in crops_data.items() if v.get("status")!="no_data" and "current_wpi" in v}
                        if valid_crops:
                            st.markdown("---"); st.markdown("**📋 Side-by-side comparison**")
                            rows = [{"Crop":cn.capitalize(),"Current WPI":ci["current_wpi"],"Hist. Avg":ci["historical_avg"],"YoY %":f"{ci['yoy_change_pct']:+.1f}%","Volatility":f"{ci['volatility_score']}/10","Best Month":ci["best_selling_month"],"Recommendation":ci["market_action"]} for cn,ci in valid_crops.items()]
                            st.dataframe(pd.DataFrame(rows).set_index("Crop"), use_container_width=True)
                    elif a5 and a5.get("error"):
                        st.error(f"Marketing agent error: {a5['error']}")
                    else:
                        st.warning("Marketing agent returned no data.")

                    # ── Agent 6 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>💰 Agent 6 — Financial Intelligence</div>", unsafe_allow_html=True)
                    if a6 and a6.get("status")=="success":
                        region     = a6.get("region","—"); land_type = a6.get("land_type","—")
                        season_str = a6.get("season","—"); total_ha  = a6.get("total_area_hectare",0)
                        best_fin   = a6.get("best_financial_crop","—")
                        portfolio  = a6.get("portfolio_summary",{}); crops_fin = a6.get("crops",{})
                        port_profit = portfolio.get("total_profit",0)
                        profit_icon = "📈" if port_profit >= 0 else "📉"
                        st.markdown(f"""
                        <div class='summary-box'>
                            <div style='font-size:22px;font-weight:700;margin-bottom:8px;'>{profit_icon} Financial Summary — {region}</div>
                            <div style='display:flex;gap:40px;flex-wrap:wrap;'>
                                <div><div style='font-size:13px;opacity:.8;'>Total Area</div><div style='font-size:20px;font-weight:600;'>{total_ha} ha</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Best Crop</div><div style='font-size:20px;font-weight:600;'>{(best_fin or '—').capitalize()}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Portfolio Revenue</div><div style='font-size:20px;font-weight:600;'>₹{portfolio.get('total_revenue',0):,.0f}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Portfolio Cost</div><div style='font-size:20px;font-weight:600;'>₹{portfolio.get('total_cost',0):,.0f}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Portfolio Profit</div><div style='font-size:20px;font-weight:600;'>₹{port_profit:,.0f}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Land / Season</div><div style='font-size:20px;font-weight:600;'>{land_type} · {season_str}</div></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        fm1,fm2,fm3,fm4 = st.columns(4)
                        fm1.metric("Total Area (ha)",f"{total_ha} ha")
                        fm2.metric("Total Revenue",  f"₹{portfolio.get('total_revenue',0):,.0f}")
                        fm3.metric("Total Cost",     f"₹{portfolio.get('total_cost',0):,.0f}")
                        fm4.metric("Net Profit",     f"₹{port_profit:,.0f}", delta=f"{'profit' if port_profit>=0 else 'loss'}")
                        if crops_fin:
                            st.markdown("**📊 Crop-wise Financial Comparison**")
                            chart_rows = [{"Crop":cn.capitalize(),"Revenue":ci.get("revenue",0),"Cost":ci.get("total_cost",0),"Profit":ci.get("profit",0)} for cn,ci in crops_fin.items()]
                            st.bar_chart(pd.DataFrame(chart_rows).set_index("Crop")[["Revenue","Cost","Profit"]], use_container_width=True, height=300)
                        st.markdown("**🌾 Per-crop Breakdown**")
                        for crop_name, ci in crops_fin.items():
                            profit = ci.get("profit",0); roi = ci.get("roi_pct",0)
                            with st.expander(f"{'✅' if profit>0 else '❌'} {crop_name.capitalize()} — Profit: ₹{profit:,.0f} | ROI: {roi:+.1f}%", expanded=(crop_name.lower()==(best_fin or "").lower())):
                                cf1,cf2,cf3,cf4,cf5 = st.columns(5)
                                cf1.metric("Area",          f"{ci.get('area_hectare','—')} ha")
                                cf2.metric("Yield",         ci.get("yield_per_ha","—"))
                                cf3.metric("Total Yield",   ci.get("total_yield","—"))
                                cf4.metric("Price/Quintal", f"₹{ci.get('price_per_quintal','—')}")
                                cf5.metric("Break-even",    ci.get("break_even_yield","—"))
                                cf6,cf7,cf8 = st.columns(3)
                                cf6.metric("Total Cost",    f"₹{ci.get('total_cost',0):,.0f}")
                                cf7.metric("Revenue",       f"₹{ci.get('revenue',0):,.0f}")
                                cf8.metric("Profit / Loss", f"₹{profit:,.0f}", delta=f"ROI {roi:+.1f}%")
                                cost_bd = ci.get("cost_breakdown",{})
                                if cost_bd:
                                    st.markdown("**Cost breakdown (INR)**")
                                    cbd_df = pd.DataFrame([{"Component":k.capitalize(),"INR":v} for k,v in cost_bd.items()]).set_index("Component")
                                    st.bar_chart(cbd_df, use_container_width=True, height=180)
                                asmp = ci.get("assumptions",{})
                                if asmp:
                                    st.markdown("**Assumptions**")
                                    ac1,ac2,ac3 = st.columns(3)
                                    ac1.caption(f"WPI used: {asmp.get('wpi_used','—')}")
                                    ac2.caption(f"Hist. avg WPI: {asmp.get('historical_avg_wpi','—')}")
                                    ac3.caption(f"YoY price: {asmp.get('yoy_price_change','—')}")
                        st.markdown("---")
                        st.markdown("**📋 Full Financial Table**")
                        table_rows = [{"Crop":cn.capitalize(),"Area (ha)":ci.get("area_hectare","—"),"Yield/ha":ci.get("yield_per_ha","—"),"Total Yield":ci.get("total_yield","—"),"Price/Quintal":f"₹{ci.get('price_per_quintal','—')}","Total Cost (₹)":f"{ci.get('total_cost',0):,.0f}","Revenue (₹)":f"{ci.get('revenue',0):,.0f}","Profit (₹)":f"{ci.get('profit',0):,.0f}","ROI %":f"{ci.get('roi_pct',0):+.1f}%","Break-even":ci.get("break_even_yield","—")} for cn,ci in crops_fin.items()]
                        st.dataframe(pd.DataFrame(table_rows).set_index("Crop"), use_container_width=True)
                    elif a6 and a6.get("error"):
                        st.error(f"Financial agent error: {a6['error']}")
                    else:
                        st.warning("Financial agent returned no data.")

                    # ════════════════════════════════════════════
                    # ── Agent 7: EDA ─────────────────────────────
                    # ════════════════════════════════════════════
                    st.markdown("---")
                    st.markdown("<div class='eda-header'>🔬 Agent 7 — Exploratory Data Analysis</div>", unsafe_allow_html=True)

                    if a7 and a7.get("status") == "success":
                        geo_eda  = a7.get("geo", {})
                        soil_eda = a7.get("soil", {})
                        yld_eda  = a7.get("yield", {})
                        mkt_eda  = a7.get("market", {})
                        fin_eda  = a7.get("financial", {})
                        cross    = a7.get("cross", {})

                        st.caption(f"Generated: {a7.get('generated','—')}")

                        # ── EDA 1: Climate ────────────────────────
                        with st.expander("🌦️ Climate & Geo EDA", expanded=True):
                            cur = geo_eda.get("current", {})
                            e1,e2,e3,e4 = st.columns(4)
                            e1.metric("Heat Index",    f"{cur.get('heat_index','—')} °C")
                            e2.metric("Aridity Index", f"{cur.get('aridity_index','—')}")
                            e3.metric("Area",          f"{geo_eda.get('area_hectare','—')} ha")
                            e4.metric("Farming Score", f"{geo_eda.get('geo_scores',{}).get('farming_score','—')} / 10")

                            fc = geo_eda.get("forecast_chart", [])
                            if fc:
                                st.markdown("**7-day temperature range & rainfall**")
                                fc_df = pd.DataFrame(fc).set_index("day")
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("*Temperature max/min (°C)*")
                                    st.line_chart(fc_df[["t_max","t_min"]].dropna(), height=200, use_container_width=True)
                                with col_b:
                                    st.markdown("*Daily temp spread & rainfall (mm)*")
                                    st.bar_chart(fc_df[["spread","rain"]].dropna(), height=200, use_container_width=True)

                            fstats = geo_eda.get("forecast_stats", {})
                            if fstats:
                                st.markdown("**Forecast descriptive stats**")
                                stat_rows = []
                                for key, sd in fstats.items():
                                    if sd:
                                        stat_rows.append({"Variable": key.replace("_"," ").title(), "Mean": sd.get("mean","—"), "Median": sd.get("median","—"), "Min": sd.get("min","—"), "Max": sd.get("max","—"), "Std Dev": sd.get("stdev","—")})
                                if stat_rows:
                                    st.dataframe(pd.DataFrame(stat_rows).set_index("Variable"), use_container_width=True)

                            for tip in geo_eda.get("insights", []):
                                st.markdown(f"<div class='insight-box'>{tip}</div>", unsafe_allow_html=True)

                        # ── EDA 2: Soil ───────────────────────────
                        with st.expander("🧪 Soil Profile EDA", expanded=True):
                            npk   = soil_eda.get("npk", {})
                            bal   = soil_eda.get("npk_balance", {})
                            gaps  = soil_eda.get("fertiliser_gaps", {})

                            s1,s2,s3,s4 = st.columns(4)
                            s1.metric("Nitrogen",   f"{npk.get('N','—')} kg/ha")
                            s2.metric("Phosphorus", f"{npk.get('P','—')} kg/ha")
                            s3.metric("Potassium",  f"{npk.get('K','—')} kg/ha")
                            s4.metric("pH Class",   soil_eda.get("ph_class","—"))

                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.markdown("**NPK share (%)**")
                                if bal:
                                    bal_df = pd.DataFrame([{"Nutrient": k, "Share %": v} for k,v in bal.items()]).set_index("Nutrient")
                                    st.bar_chart(bal_df, height=200, use_container_width=True)
                            with col_b:
                                st.markdown("**Fertiliser gap vs ideal (kg/ha)**")
                                if gaps:
                                    gap_df = pd.DataFrame([{"Nutrient": k, "Deficit kg/ha": v} for k,v in gaps.items()]).set_index("Nutrient")
                                    st.bar_chart(gap_df, height=200, use_container_width=True)

                            radar = soil_eda.get("nutrient_radar", [])
                            if radar:
                                st.markdown("**Actual vs ideal nutrient levels**")
                                rad_df = pd.DataFrame(radar).set_index("nutrient")
                                st.bar_chart(rad_df[["value","ideal"]], height=220, use_container_width=True)

                            for tip in soil_eda.get("insights", []):
                                st.markdown(f"<div class='insight-box'>{tip}</div>", unsafe_allow_html=True)

                        # ── EDA 3: Yield ──────────────────────────
                        with st.expander("📈 Yield Analysis EDA", expanded=True):
                            ystats = yld_eda.get("stats", {})
                            if ystats:
                                y1,y2,y3,y4 = st.columns(4)
                                y1.metric("Mean yield",   f"{ystats.get('mean','—')} t/ha")
                                y2.metric("Median yield", f"{ystats.get('median','—')} t/ha")
                                y3.metric("Best yield",   f"{ystats.get('max','—')} t/ha")
                                y4.metric("Std deviation",f"{ystats.get('stdev','—')} t/ha")

                            yc = yld_eda.get("yield_chart", [])
                            if yc:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**Yield per hectare by crop**")
                                    yc_df = pd.DataFrame(yc).set_index("crop")
                                    st.bar_chart(yc_df["yield_per_ha"], height=250, use_container_width=True)
                                with col_b:
                                    st.markdown("**Total yield (tonnes) by crop**")
                                    st.bar_chart(yc_df["total_yield"], height=250, use_container_width=True)

                            gaps_y = yld_eda.get("yield_gaps", {})
                            if gaps_y:
                                st.markdown("**Yield gap vs best crop (t/ha)**")
                                gap_df = pd.DataFrame([{"Crop": c, "Gap t/ha": v} for c,v in gaps_y.items()]).set_index("Crop")
                                st.bar_chart(gap_df, height=200, use_container_width=True)

                            for tip in yld_eda.get("insights", []):
                                st.markdown(f"<div class='insight-box'>{tip}</div>", unsafe_allow_html=True)

                        # ── EDA 4: Market ─────────────────────────
                        with st.expander("💹 Market / WPI EDA", expanded=True):
                            msum = mkt_eda.get("summary", [])
                            if msum:
                                msum_df = pd.DataFrame(msum)
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**Current WPI vs historical average**")
                                    wpi_df = msum_df[["crop","current_wpi","historical_avg"]].set_index("crop")
                                    st.bar_chart(wpi_df, height=250, use_container_width=True)
                                with col_b:
                                    st.markdown("**YoY price change (%)**")
                                    yoy_df = msum_df[["crop","yoy_pct"]].set_index("crop")
                                    st.bar_chart(yoy_df, height=250, use_container_width=True)

                                st.markdown("**Volatility scores (1=low, 10=high)**")
                                vol_df = msum_df[["crop","volatility"]].set_index("crop")
                                st.bar_chart(vol_df, height=180, use_container_width=True)

                                st.markdown("**Market action distribution**")
                                adist = mkt_eda.get("action_dist", {})
                                if adist:
                                    ad_df = pd.DataFrame([{"Action": k, "Count": v} for k,v in adist.items() if v > 0]).set_index("Action")
                                    st.bar_chart(ad_df, height=160, use_container_width=True)

                            # WPI 12-month trend for all crops together
                            trend_data = mkt_eda.get("trend_data", {})
                            if trend_data:
                                st.markdown("**WPI 12-month trend — all crops**")
                                all_trends = {}
                                for cn, td in trend_data.items():
                                    try:
                                        s = pd.DataFrame(td).set_index("month")["wpi"].rename(cn)
                                        all_trends[cn] = s
                                    except Exception:
                                        pass
                                if all_trends:
                                    trend_combined = pd.concat(all_trends.values(), axis=1)
                                    st.line_chart(trend_combined, height=280, use_container_width=True)

                            for tip in mkt_eda.get("insights", []):
                                st.markdown(f"<div class='insight-box'>{tip}</div>", unsafe_allow_html=True)

                        # ── EDA 5: Financial ──────────────────────
                        with st.expander("💰 Financial EDA", expanded=True):
                            fstats = fin_eda.get("stats", {})
                            if fstats:
                                st.markdown("**Descriptive statistics across all crops**")
                                stat_rows = []
                                for key, sd in fstats.items():
                                    if sd:
                                        stat_rows.append({"Metric": key.capitalize(), "Mean": f"₹{sd.get('mean',0):,.0f}", "Median": f"₹{sd.get('median',0):,.0f}", "Min": f"₹{sd.get('min',0):,.0f}", "Max": f"₹{sd.get('max',0):,.0f}", "Std Dev": f"₹{sd.get('stdev',0):,.0f}"})
                                if stat_rows:
                                    st.dataframe(pd.DataFrame(stat_rows).set_index("Metric"), use_container_width=True)

                            fin_rows = fin_eda.get("rows", [])
                            if fin_rows:
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.markdown("**Profit ranking by crop**")
                                    rank_df = pd.DataFrame(fin_eda.get("ranking", [])).set_index("crop") if fin_eda.get("ranking") else pd.DataFrame(fin_rows).set_index("crop")
                                    st.bar_chart(pd.DataFrame(fin_rows).set_index("crop")["profit"], height=250, use_container_width=True)
                                with col_b:
                                    st.markdown("**ROI % by crop**")
                                    roi_df = pd.DataFrame(fin_rows)[["crop","roi"]].set_index("crop")
                                    st.bar_chart(roi_df, height=250, use_container_width=True)

                                st.markdown("**Gross margin % vs cost % by crop**")
                                md = fin_eda.get("margin_data", [])
                                if md:
                                    md_df = pd.DataFrame(md).set_index("crop")
                                    st.bar_chart(md_df[["gross_margin","cost_pct"]], height=220, use_container_width=True)

                            cost_split = fin_eda.get("avg_cost_split", {})
                            if cost_split:
                                st.markdown("**Average cost component breakdown (₹)**")
                                cs_df = pd.DataFrame([{"Component": k.capitalize(), "Avg INR": v} for k,v in cost_split.items()]).set_index("Component")
                                st.bar_chart(cs_df, height=220, use_container_width=True)

                            for tip in fin_eda.get("insights", []):
                                st.markdown(f"<div class='insight-box'>{tip}</div>", unsafe_allow_html=True)

                        # ── EDA 6: Cross-agent insights ───────────
                        with st.expander("🔗 Cross-Agent Insights & Alignment", expanded=True):
                            col_a, col_b = st.columns(2)
                            col_a.metric("Alignment signals", f"{cross.get('alignment_score',0)} ✅")
                            col_b.metric("Risk flags",        f"{cross.get('risk_flags',0)} ⚠️")
                            for note in cross.get("notes", []):
                                css = "cross-box" if ("⚠️" in note or "❌" in note or "🌡️" in note) else "insight-box"
                                st.markdown(f"<div class='{css}'>{note}</div>", unsafe_allow_html=True)

                    elif a7 and a7.get("error"):
                        st.error(f"EDA error: {a7.get('error')}")
                        with st.expander("Trace"):
                            st.code(a7.get("trace",""))
                    else:
                        st.warning("EDA agent returned no data.")

                    # ════════════════════════════════════════════
                    # ── Dashboard ─────────────────────────────────
                    # ════════════════════════════════════════════
                    st.markdown("---")
                    st.markdown("<div class='dash-header'>📊 Dashboard — Summary View</div>", unsafe_allow_html=True)

                    if a6 and a6.get("status")=="success" and a7 and a7.get("status")=="success":
                        portfolio  = a6.get("portfolio_summary", {})
                        crops_fin  = a6.get("crops", {})
                        geo_scores = a7.get("geo", {}).get("geo_scores", {})
                        cross      = a7.get("cross", {})

                        # ── Top KPI row ───────────────────────────
                        st.markdown("#### Key Performance Indicators")
                        k1,k2,k3,k4,k5,k6 = st.columns(6)
                        k1.metric("Net Profit",      f"₹{portfolio.get('total_profit',0):,.0f}")
                        k2.metric("Total Revenue",   f"₹{portfolio.get('total_revenue',0):,.0f}")
                        k3.metric("Portfolio ROI",   f"{portfolio.get('portfolio_roi_pct',0):.1f}%")
                        k4.metric("Farming Score",   f"{geo_scores.get('farming_score','—')} / 10")
                        k5.metric("Alignment",       f"{cross.get('alignment_score',0)} ✅")
                        k6.metric("Risk Flags",      f"{cross.get('risk_flags',0)} ⚠️")

                        # ── Crop comparison table ─────────────────
                        st.markdown("#### Crop Performance Summary")
                        dash_rows = []
                        for cn, ci in crops_fin.items():
                            wpi_info = a5.get("crops",{}).get(cn, {})
                            dash_rows.append({
                                "Crop":         cn.capitalize(),
                                "Yield (t/ha)": ci.get("yield_per_ha","—"),
                                "Revenue (₹)":  f"{ci.get('revenue',0):,.0f}",
                                "Cost (₹)":     f"{ci.get('total_cost',0):,.0f}",
                                "Profit (₹)":   f"{ci.get('profit',0):,.0f}",
                                "ROI %":        f"{ci.get('roi_pct',0):+.1f}%",
                                "WPI":          wpi_info.get("current_wpi","—"),
                                "Market":       wpi_info.get("market_action","—"),
                            })
                        st.dataframe(pd.DataFrame(dash_rows).set_index("Crop"), use_container_width=True)

                        # ── Visual summary ────────────────────────
                        st.markdown("#### Visual Summary")
                        d1, d2 = st.columns(2)
                        with d1:
                            st.markdown("**Revenue vs Cost vs Profit (₹)**")
                            chart_data = pd.DataFrame([{"Crop":cn.capitalize(),"Revenue":ci.get("revenue",0),"Cost":ci.get("total_cost",0),"Profit":ci.get("profit",0)} for cn,ci in crops_fin.items()]).set_index("Crop")
                            st.bar_chart(chart_data, height=280, use_container_width=True)
                        with d2:
                            st.markdown("**ROI % by crop**")
                            roi_data = pd.DataFrame([{"Crop":cn.capitalize(),"ROI %":ci.get("roi_pct",0)} for cn,ci in crops_fin.items()]).set_index("Crop")
                            st.bar_chart(roi_data, height=280, use_container_width=True)

                        # ── Recommendation box ────────────────────
                        fin_eda = a7.get("financial", {})
                        cross   = a7.get("cross", {})
                        best_fin_crop = a6.get("best_financial_crop","—")
                        best_mkt_crop = a5.get("best_market_crop","—")

                        st.markdown("#### Smart Recommendation")
                        if best_fin_crop.lower() == best_mkt_crop.lower():
                            st.success(f"🎯 **{best_fin_crop.capitalize()}** is your best choice — highest profit AND best market timing. Plant maximum area in this crop.")
                        else:
                            st.info(f"💡 **Financially strongest:** {best_fin_crop.capitalize()} | **Best market timing:** {best_mkt_crop.capitalize()} — consider splitting area between both.")

                        for note in cross.get("notes", []):
                            if "✅" in note or "🎯" in note:
                                st.success(note)
                            elif "⚠️" in note or "❌" in note:
                                st.warning(note)
                            else:
                                st.info(note)
                    else:
                        st.warning("Dashboard requires Agent 6 and Agent 7 to complete successfully.")

                    # ── Full JSON ─────────────────────────────────
                    st.markdown("---")
                    with st.expander("Full JSON output"):
                        st.json(result)

                    st.session_state.update({
                        "agent1_output": a1, "agent2_output": a2,
                        "agent3_output": a3, "agent4_output": a4,
                        "agent5_output": a5, "agent6_output": a6,
                        "agent7_eda":    a7,
                    })
                    st.success("Full pipeline complete: Geo → Climate → Soil → Yield → Market → Finance → EDA → Dashboard 🚀")

            except requests.exceptions.ConnectionError:
                st.error("Cannot reach Flask server. Make sure `python app.py` is running.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")