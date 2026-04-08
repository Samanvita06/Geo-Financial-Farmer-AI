# ui.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import math

st.set_page_config(page_title="AgriMineral Pipeline", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size:40px; font-weight:700; color:#2E7D32; }
    .crop-card {
        background: linear-gradient(135deg,#e8f5e9,#f1f8e9);
        border-left:4px solid #2E7D32;
        padding:12px 16px; border-radius:10px; margin-bottom:10px; font-size:14px;
    }
    .agent-header {
        background-color:#2E7D32; color:white; padding:8px 14px;
        border-radius:8px; font-weight:600; font-size:16px;
        display:inline-block; margin-bottom:10px;
    }
    .market-card {
        background:linear-gradient(135deg,#fff8e1,#fffde7);
        border-left:4px solid #f9a825; padding:14px 18px;
        border-radius:10px; margin-bottom:12px; font-size:14px;
    }
    .action-sell  { background:#e8f5e9; border-left:5px solid #2e7d32; padding:10px 14px; border-radius:8px; font-weight:600; font-size:15px; margin-bottom:8px; }
    .action-hold  { background:#fff8e1; border-left:5px solid #f9a825; padding:10px 14px; border-radius:8px; font-weight:600; font-size:15px; margin-bottom:8px; }
    .action-store { background:#fce4ec; border-left:5px solid #c62828; padding:10px 14px; border-radius:8px; font-weight:600; font-size:15px; margin-bottom:8px; }
    .fin-profit   { background:#e8f5e9; border-left:5px solid #2e7d32; padding:14px 18px; border-radius:10px; margin-bottom:10px; }
    .fin-loss     { background:#fce4ec; border-left:5px solid #c62828; padding:14px 18px; border-radius:10px; margin-bottom:10px; }
    .fin-neutral  { background:#e3f2fd; border-left:5px solid #1565c0; padding:14px 18px; border-radius:10px; margin-bottom:10px; }
    .summary-box  {
        background:linear-gradient(135deg,#1b5e20,#2e7d32); color:white;
        padding:20px 24px; border-radius:14px; margin-bottom:16px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>🌱 AgriMineral Land Analyzer</div>", unsafe_allow_html=True)
st.caption("AI-powered Geo-Spatial Farming Intelligence")

# ── Step 1: City Search ──────────────────────────────────────────
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

# ── Step 2: Map ──────────────────────────────────────────────────
st.subheader("Step 2 — Select land region")
st.caption("Draw a rectangle on the map to select your land area")
m = folium.Map(location=[lat, lon], zoom_start=12 if city_found else 5)
folium.plugins.Draw(
    export=False,
    draw_options={"rectangle":True,"polygon":False,"circle":False,"marker":False,"polyline":False,"circlemarker":False},
    edit_options={"edit": False}
).add_to(m)
map_output = st_folium(m, width=None, height=500, returned_objects=["last_active_drawing"])

# ── Step 3: Selection ────────────────────────────────────────────
bounds = None
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
        "area_km2":area
    }

    st.subheader("Step 3 — Selected region")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Center lat",clat); c2.metric("Center lon",clon)
    c3.metric("Area",f"{area} km²"); c4.metric("City",city or "—")

    # ── Step 4: Analyze ──────────────────────────────────────────
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
                    a1 = result.get("agent1",{})
                    a2 = result.get("agent2",{})
                    a3 = result.get("agent3_soil",{})
                    a4 = result.get("agent4_yield",{})
                    a5 = result.get("agent5_marketing",{})
                    a6 = result.get("agent6_financial",{})

                    # ── Agent 1 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>🛰️ Agent 1 — Raw Data Collection</div>", unsafe_allow_html=True)
                    w = a1.get("weather",{}).get("current",{}); t = a1.get("terrain",{})
                    r1,r2,r3,r4 = st.columns(4)
                    r1.metric("Temperature",f"{w.get('temperature_2m','—')} °C")
                    r2.metric("Humidity",f"{w.get('relative_humidity_2m','—')} %")
                    r3.metric("Wind speed",f"{w.get('windspeed_10m','—')} km/h")
                    r4.metric("Precipitation",f"{w.get('precipitation','—')} mm")
                    r5,r6,r7,r8 = st.columns(4)
                    r5.metric("Elevation",f"{t.get('elevation_m','—')} m")
                    r6.metric("Terrain",t.get("terrain_note","—"))
                    r7.metric("Timezone",a1.get("weather",{}).get("timezone","—"))
                    r8.metric("Area selected",f"{area} km²")
                    forecast = a1.get("weather",{}).get("weekly_forecast",{})
                    if forecast:
                        st.markdown("**7-day forecast**")
                        days=forecast.get("time",[]); tmax=forecast.get("temperature_2m_max",[])
                        tmin=forecast.get("temperature_2m_min",[]); rain=forecast.get("precipitation_sum",[])
                        cols=st.columns(len(days)) if days else []
                        for i,col in enumerate(cols):
                            day=days[i].split("-")[-1] if i<len(days) else "—"
                            col.markdown(f"<div style='text-align:center;font-size:12px;'><b>{day}</b><br>{tmax[i] if i<len(tmax) else '—'}°/{tmin[i] if i<len(tmin) else '—'}°<br>{rain[i] if i<len(rain) else '—'}mm</div>",unsafe_allow_html=True)
                    maps=a1.get("maps",{})
                    if maps:
                        st.markdown("**Map links**")
                        ml1,ml2,ml3=st.columns(3)
                        ml1.link_button("OpenStreetMap",maps.get("openstreetmap","#"),use_container_width=True)
                        ml2.link_button("Google Maps",maps.get("google_maps","#"),use_container_width=True)
                        ml3.link_button("Satellite view",maps.get("satellite_view","#"),use_container_width=True)

                    # ── Agent 2 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>🌍 Agent 2 — Geo-Spatial Analysis</div>", unsafe_allow_html=True)
                    a2c1,a2c2,a2c3=st.columns(3)
                    a2c1.metric("Climate zone",a2.get("climate_zone","—"))
                    a2c2.metric("Land type",a2.get("land_type","—"))
                    a2c3.metric("Season",a2.get("current_season","—"))
                    farming_score=a2.get("farming_score",0); soil_health=a2.get("soil_health_score",0)
                    st.markdown("**Overall scores**")
                    sc1,sc2=st.columns(2)
                    with sc1:
                        st.metric("Farming suitability",f"{farming_score} / 10"); st.progress(farming_score/10)
                    with sc2:
                        st.metric("Soil health",f"{soil_health} / 10"); st.progress(soil_health/10)
                    if farming_score>=7: st.success(f"Highly suitable — {farming_score}/10")
                    elif farming_score>=5: st.warning(f"Moderately suitable — {farming_score}/10")
                    else: st.error(f"Needs treatment — {farming_score}/10")

                    # ── Agent 3 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>🧪 Agent 3 — Soil & Crop Recommendation</div>", unsafe_allow_html=True)
                    if a3:
                        sa1,sa2,sa3,sa4=st.columns(4)
                        sa1.metric("Nitrogen (N)",f"{a3.get('n','—')} kg/ha")
                        sa2.metric("Phosphorus (P)",f"{a3.get('p','—')} kg/ha")
                        sa3.metric("Potassium (K)",f"{a3.get('k','—')} kg/ha")
                        sa4.metric("Soil pH",a3.get("ph","—"))
                        st.metric("Soil type",a3.get("soil_type","—"))
                        recommended_crops=a3.get("recommended_crops",[])
                        if recommended_crops:
                            st.markdown("**🌾 Recommended crops**")
                            crop_cols=st.columns(min(len(recommended_crops),4))
                            for i,crop in enumerate(recommended_crops):
                                with crop_cols[i%4]:
                                    st.markdown(f"<div class='crop-card'>🌿 <b>{crop.capitalize()}</b></div>",unsafe_allow_html=True)
                    else:
                        st.warning("Agent 3 returned no data.")

                    # ── Agent 4 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>📈 Agent 4 — Yield Prediction</div>", unsafe_allow_html=True)
                    if a4 and a4.get("best_crop","—")!="—":
                        y1,y2,y3=st.columns(3)
                        y1.metric("Best Crop",a4.get("best_crop","—"))
                        y2.metric("Estimated Yield",a4.get("estimated_yield","—"))
                        y3.metric("Confidence",f"{a4.get('confidence',0)}%")
                        all_preds=a4.get("all_predictions",{})
                        if all_preds:
                            st.markdown("**All crop yield predictions**")
                            pred_cols=st.columns(min(len(all_preds),4))
                            for i,(crop,val) in enumerate(all_preds.items()):
                                pred_cols[i%4].metric(crop.capitalize(),val)
                    else:
                        st.warning("No yield predictions available.")

                    # ── Agent 5 ──────────────────────────────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>💹 Agent 5 — Marketing Intelligence</div>", unsafe_allow_html=True)
                    if a5 and a5.get("status")=="success":
                        crops_data=a5.get("crops",{}); best_mkt_crop=a5.get("best_market_crop","—")
                        st.info(f"📅 Analysis: **{a5.get('analysis_month','—')} {a5.get('analysis_year','—')}** | 🏆 Best opportunity: **{(best_mkt_crop or '—').capitalize()}**")
                        for crop_name,info in crops_data.items():
                            if info.get("status")=="no_data":
                                st.warning(f"⚠️ {crop_name}: {info.get('message','No data')}"); continue
                            with st.expander(f"📊 {crop_name.capitalize()}  —  WPI: {info.get('current_wpi','—')}  |  {info.get('market_action','—')}",expanded=(crop_name==best_mkt_crop)):
                                m1,m2,m3,m4,m5=st.columns(5)
                                m1.metric("Current WPI",info.get("current_wpi","—"),delta=f"{info.get('yoy_change_pct',0):+.1f}% YoY")
                                m2.metric("Historical Avg",info.get("historical_avg","—"))
                                m3.metric("Volatility",f"{info.get('volatility_score','—')} / 10")
                                m4.metric("Best Month",info.get("best_selling_month","—"))
                                m5.metric("Worst Month",info.get("worst_selling_month","—"))
                                action=info.get("market_action",""); action_col=info.get("action_color","warning")
                                css_class="action-sell" if action_col=="success" else "action-store" if action_col=="error" else "action-hold"
                                st.markdown(f"<div class='{css_class}'>Market Action: {action}</div>",unsafe_allow_html=True)
                                for r in info.get("action_reasons",[]): st.markdown(f"- {r}")
                                trend=info.get("trend_12m",[])
                                if trend:
                                    import pandas as pd
                                    trend_df=pd.DataFrame(trend).set_index("month")
                                    st.markdown(f"**WPI trend — last 12 months**")
                                    st.line_chart(trend_df,use_container_width=True,height=160)
                        valid_crops={k:v for k,v in crops_data.items() if v.get("status")!="no_data" and "current_wpi" in v}
                        if valid_crops:
                            st.markdown("---"); st.markdown("**📋 Side-by-side comparison**")
                            import pandas as pd
                            rows=[{"Crop":cn.capitalize(),"Current WPI":ci["current_wpi"],"Hist. Avg":ci["historical_avg"],"YoY %":f"{ci['yoy_change_pct']:+.1f}%","Volatility":f"{ci['volatility_score']}/10","Best Month":ci["best_selling_month"],"Recommendation":ci["market_action"]} for cn,ci in valid_crops.items()]
                            st.dataframe(pd.DataFrame(rows).set_index("Crop"),use_container_width=True)
                    elif a5 and a5.get("error"):
                        st.error(f"Marketing agent error: {a5['error']}")
                    else:
                        st.warning("Marketing agent returned no data.")

                    # ── Agent 6: FINANCIAL INTELLIGENCE ──────────
                    st.markdown("---")
                    st.markdown("<div class='agent-header'>💰 Agent 6 — Financial Intelligence</div>", unsafe_allow_html=True)

                    if a6 and a6.get("status") == "success":
                        import pandas as pd

                        region     = a6.get("region", "—")
                        land_type  = a6.get("land_type", "—")
                        season     = a6.get("season", "—")
                        total_ha   = a6.get("total_area_hectare", 0)
                        best_fin   = a6.get("best_financial_crop", "—")
                        portfolio  = a6.get("portfolio_summary", {})
                        crops_fin  = a6.get("crops", {})

                        # ── Summary card ─────────────────────────
                        port_profit = portfolio.get("total_profit", 0)
                        profit_color = "#e8f5e9" if port_profit >= 0 else "#fce4ec"
                        profit_icon  = "📈" if port_profit >= 0 else "📉"
                        st.markdown(f"""
                        <div class='summary-box'>
                            <div style='font-size:22px;font-weight:700;margin-bottom:8px;'>
                                {profit_icon} Financial Summary — {region}
                            </div>
                            <div style='display:flex;gap:40px;flex-wrap:wrap;'>
                                <div><div style='font-size:13px;opacity:.8;'>Total Area</div><div style='font-size:20px;font-weight:600;'>{total_ha} ha</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Best Crop</div><div style='font-size:20px;font-weight:600;'>{(best_fin or '—').capitalize()}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Portfolio Revenue</div><div style='font-size:20px;font-weight:600;'>₹{portfolio.get('total_revenue',0):,.0f}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Portfolio Cost</div><div style='font-size:20px;font-weight:600;'>₹{portfolio.get('total_cost',0):,.0f}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Portfolio Profit</div><div style='font-size:20px;font-weight:600;'>₹{port_profit:,.0f}</div></div>
                                <div><div style='font-size:13px;opacity:.8;'>Land / Season</div><div style='font-size:20px;font-weight:600;'>{land_type} · {season}</div></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # ── Top-level metrics ─────────────────────
                        fm1,fm2,fm3,fm4 = st.columns(4)
                        fm1.metric("Total Area (ha)",    f"{total_ha} ha")
                        fm2.metric("Total Revenue",      f"₹{portfolio.get('total_revenue',0):,.0f}")
                        fm3.metric("Total Cost",         f"₹{portfolio.get('total_cost',0):,.0f}")
                        fm4.metric("Net Profit",         f"₹{port_profit:,.0f}",
                                   delta=f"{'profit' if port_profit>=0 else 'loss'}")

                        # ── Comparison bar chart ──────────────────
                        if crops_fin:
                            st.markdown("**📊 Crop-wise Financial Comparison**")
                            chart_rows = []
                            for cn, ci in crops_fin.items():
                                chart_rows.append({
                                    "Crop":    cn.capitalize(),
                                    "Revenue": ci.get("revenue", 0),
                                    "Cost":    ci.get("total_cost", 0),
                                    "Profit":  ci.get("profit", 0),
                                })
                            chart_df = pd.DataFrame(chart_rows).set_index("Crop")
                            st.bar_chart(chart_df[["Revenue","Cost","Profit"]], use_container_width=True, height=300)

                        # ── Per-crop financial cards ──────────────
                        st.markdown("**🌾 Per-crop Breakdown**")
                        for crop_name, ci in crops_fin.items():
                            profit     = ci.get("profit", 0)
                            css_class  = "fin-profit" if profit > 0 else "fin-loss"
                            profit_str = f"₹{profit:,.0f}"
                            roi        = ci.get("roi_pct", 0)

                            with st.expander(
                                f"{'✅' if profit>0 else '❌'} {crop_name.capitalize()}  —  "
                                f"Profit: {profit_str}  |  ROI: {roi:+.1f}%",
                                expanded=(crop_name.lower() == (best_fin or "").lower())
                            ):
                                # Main metrics
                                cf1,cf2,cf3,cf4,cf5 = st.columns(5)
                                cf1.metric("Area",        f"{ci.get('area_hectare','—')} ha")
                                cf2.metric("Yield",       ci.get("yield_per_ha","—"))
                                cf3.metric("Total Yield", ci.get("total_yield","—"))
                                cf4.metric("Price/Quintal", f"₹{ci.get('price_per_quintal','—')}")
                                cf5.metric("Break-even",  ci.get("break_even_yield","—"))

                                cf6,cf7,cf8 = st.columns(3)
                                cf6.metric("Total Cost",    f"₹{ci.get('total_cost',0):,.0f}")
                                cf7.metric("Revenue",       f"₹{ci.get('revenue',0):,.0f}")
                                cf8.metric("Profit / Loss", profit_str,
                                           delta=f"ROI {roi:+.1f}%")

                                # Cost breakdown donut data as bar chart
                                cost_bd = ci.get("cost_breakdown", {})
                                if cost_bd:
                                    st.markdown("**Cost breakdown (INR)**")
                                    cbd_df = pd.DataFrame(
                                        [{"Component": k.capitalize(), "INR": v} for k, v in cost_bd.items()]
                                    ).set_index("Component")
                                    st.bar_chart(cbd_df, use_container_width=True, height=180)

                                # Assumptions
                                asmp = ci.get("assumptions", {})
                                if asmp:
                                    st.markdown("**Assumptions**")
                                    ac1,ac2,ac3 = st.columns(3)
                                    ac1.caption(f"WPI used: {asmp.get('wpi_used','—')}")
                                    ac2.caption(f"Hist. avg WPI: {asmp.get('historical_avg_wpi','—')}")
                                    ac3.caption(f"YoY price: {asmp.get('yoy_price_change','—')}")

                        # ── Tabular summary ───────────────────────
                        st.markdown("---")
                        st.markdown("**📋 Full Financial Table**")
                        table_rows = []
                        for cn, ci in crops_fin.items():
                            table_rows.append({
                                "Crop":            cn.capitalize(),
                                "Area (ha)":       ci.get("area_hectare","—"),
                                "Yield/ha":        ci.get("yield_per_ha","—"),
                                "Total Yield":     ci.get("total_yield","—"),
                                "Price/Quintal":   f"₹{ci.get('price_per_quintal','—')}",
                                "Total Cost (₹)":  f"{ci.get('total_cost',0):,.0f}",
                                "Revenue (₹)":     f"{ci.get('revenue',0):,.0f}",
                                "Profit (₹)":      f"{ci.get('profit',0):,.0f}",
                                "ROI %":           f"{ci.get('roi_pct',0):+.1f}%",
                                "Break-even":      ci.get("break_even_yield","—"),
                            })
                        fin_df = pd.DataFrame(table_rows).set_index("Crop")
                        st.dataframe(fin_df, use_container_width=True)

                    elif a6 and a6.get("error"):
                        st.error(f"Financial agent error: {a6['error']}")
                    else:
                        st.warning("Financial agent returned no data.")

                    # ── Full JSON ─────────────────────────────────
                    st.markdown("---")
                    with st.expander("Full JSON output"):
                        st.json(result)

                    st.session_state.update({
                        "agent1_output": a1, "agent2_output": a2,
                        "agent3_output": a3, "agent4_output": a4,
                        "agent5_output": a5, "agent6_output": a6,
                    })
                    st.success("Full pipeline complete: Geo → Climate → Soil → Yield → Market → Finance 🚀")

            except requests.exceptions.ConnectionError:
                st.error("Cannot reach Flask server. Make sure `python app.py` is running.")
            except Exception as e:
                st.error(f"Something went wrong: {e}")