"""
routing_page.py
Vehicle Routing Optimization page — rendered via Streamlit HTML component (Leaflet.js).
No extra pip packages needed for the map — uses st.components.v1.html().
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

from vehicle_routing import (
    optimize_day, TRAFFIC_FACTORS,
    DRIVER_COST_PER_HOUR, FUEL_COST_PER_HOUR,
    AVG_SPEED_KMPH, TRUCK_CAPACITY_M3,
    DEPOT_LAT, DEPOT_LNG, DEPOT_NAME,
)

ROUTE_DATA = "route_data_march2026.csv"

TRUCK_COLORS = [
    "#f97316","#38bdf8","#22d3a0","#a78bfa",
    "#fb923c","#34d399","#60a5fa","#f472b6",
]

# ── Load route data ────────────────────────────────────────────────────────────
@st.cache_data
def load_route_data() -> pd.DataFrame:
    if not os.path.exists(ROUTE_DATA):
        st.error(f"Missing `{ROUTE_DATA}`. Run `python3 generate_route_data.py` first.")
        return pd.DataFrame()
    df = pd.read_csv(ROUTE_DATA, parse_dates=["date"])
    df["qty_m3"] = pd.to_numeric(df["qty_m3"], errors="coerce").fillna(0)
    df["lat"]    = pd.to_numeric(df["lat"],    errors="coerce")
    df["lng"]    = pd.to_numeric(df["lng"],    errors="coerce")
    df = df.dropna(subset=["lat","lng"])
    return df


def render_leaflet_map(result: dict, selected_date: str) -> str:
    """Build self-contained Leaflet HTML for embedding in st.components.v1.html()"""
    route   = result["route"]
    trucks  = result["trucks"]
    poly    = result["polyline"]

    # Markers JSON
    markers = []
    for i, stop in enumerate(route):
        truck_idx = next((ti for ti, t in enumerate(trucks) if stop in t), 0)
        color = TRUCK_COLORS[truck_idx % len(TRUCK_COLORS)]
        markers.append({
            "lat": stop["lat"], "lng": stop["lng"],
            "name": stop["client_name"],
            "addr": stop.get("project_address",""),
            "qty":  stop.get("qty_m3", 0),
            "psi":  stop.get("psi", ""),
            "pump": stop.get("pump_status",""),
            "order": i + 1,
            "color": color,
            "truck": truck_idx + 1,
        })

    # Polyline as JS array
    poly_js = json.dumps(poly)
    markers_js = json.dumps(markers)
    depot_js = json.dumps({"lat": DEPOT_LAT, "lng": DEPOT_LNG, "name": DEPOT_NAME})

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:#060a10; font-family:'IBM Plex Mono',monospace; }}
  #map {{ width:100%; height:580px; border-radius:12px; }}
  .legend {{
    background: rgba(13,20,32,0.95);
    border: 1px solid #1e3050;
    border-radius:8px;
    padding:10px 14px;
    font-size:12px;
    color:#e2e8f0;
    line-height:1.8;
  }}
  .legend-title {{ font-weight:600; color:#f97316; margin-bottom:6px; font-size:13px; }}
  .dot {{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }}
  .popup-inner {{ font-family:'IBM Plex Mono',monospace; font-size:12px; color:#1e293b; min-width:200px; }}
  .popup-header {{ font-weight:700; font-size:13px; color:#f97316; margin-bottom:4px; }}
  .popup-row {{ display:flex; justify-content:space-between; gap:12px; padding:2px 0; border-bottom:1px solid #e2e8f0; }}
</style>
</head>
<body>
<div id="map"></div>
<script>
const depot   = {depot_js};
const markers = {markers_js};
const polyline= {poly_js};
const colors  = {json.dumps(TRUCK_COLORS)};

const map = L.map('map', {{
  center: [23.83, 90.37],
  zoom: 11,
  zoomControl: true,
}});

// OpenStreetMap tiles (free, no API key)
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  attribution: '© <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>',
  maxZoom: 19,
}}).addTo(map);

// Route polyline
if (polyline && polyline.length > 1) {{
  L.polyline(polyline, {{
    color: '#f97316',
    weight: 3.5,
    opacity: 0.85,
    dashArray: '6,4',
  }}).addTo(map);
}}

// Depot marker
const depotIcon = L.divIcon({{
  html: `<div style="background:#22d3a0;color:#060a10;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:14px;border:2px solid #fff;box-shadow:0 2px 8px rgba(0,0,0,0.5)">D</div>`,
  className: '', iconSize:[28,28], iconAnchor:[14,14], popupAnchor:[0,-14],
}});
L.marker([depot.lat, depot.lng], {{icon: depotIcon}})
  .addTo(map)
  .bindPopup(`<div class='popup-inner'><div class='popup-header'>🏭 DEPOT</div><div>${{depot.name}}</div></div>`);

// Delivery markers
markers.forEach((m, idx) => {{
  const icon = L.divIcon({{
    html: `<div style="background:${{m.color}};color:#fff;border-radius:50%;width:26px;height:26px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:11px;border:2px solid rgba(255,255,255,0.7);box-shadow:0 2px 8px rgba(0,0,0,0.5)">${{m.order}}</div>`,
    className: '', iconSize:[26,26], iconAnchor:[13,13], popupAnchor:[0,-13],
  }});
  L.marker([m.lat, m.lng], {{icon}})
    .addTo(map)
    .bindPopup(`
      <div class='popup-inner'>
        <div class='popup-header'>#${{m.order}} — ${{m.name}}</div>
        <div class='popup-row'><span>📍 Address</span><span style='text-align:right;max-width:140px'>${{m.addr}}</span></div>
        <div class='popup-row'><span>📦 Qty</span><span>${{m.qty.toFixed(2)}} m³</span></div>
        <div class='popup-row'><span>💪 PSI</span><span>${{m.psi}}</span></div>
        <div class='popup-row'><span>🚿 Pump</span><span>${{m.pump}}</span></div>
        <div class='popup-row'><span>🚛 Truck</span><span>Truck ${{m.truck}}</span></div>
      </div>
    `);
}});

// Legend
const legend = L.control({{position: 'bottomright'}});
legend.onAdd = function() {{
  const div = L.DomUtil.create('div','legend');
  const truckNums = [...new Set(markers.map(m => m.truck))].sort();
  div.innerHTML = `<div class='legend-title'>🚛 Route Legend</div>`;
  div.innerHTML += `<div><span class='dot' style='background:#22d3a0'></span> Depot</div>`;
  truckNums.forEach(t => {{
    const col = colors[(t-1) % colors.length];
    div.innerHTML += `<div><span class='dot' style='background:${{col}}'></span> Truck ${{t}}</div>`;
  }});
  div.innerHTML += `<div style='margin-top:6px;color:#64748b;font-size:11px'>Numbers = delivery order</div>`;
  return div;
}};
legend.addTo(map);

// Fit bounds
const allPts = markers.map(m => [m.lat, m.lng]).concat([[depot.lat, depot.lng]]);
if (allPts.length > 1) map.fitBounds(allPts, {{padding:[30,30]}});
</script>
</body>
</html>
"""
    return html


def render_routing_page():
    st.markdown("# 🚛 Route Optimizer")
    st.markdown('<div style="color:#64748b;font-size:.82rem;margin-top:-12px;margin-bottom:20px;">Transport cost optimization · OpenStreetMap routing · Full March 2026</div>', unsafe_allow_html=True)

    df = load_route_data()
    if df.empty:
        st.error("Route data not found. Run `python3 generate_route_data.py` in your terminal first.")
        return

    # ── Controls ─────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 2])

    available_dates = sorted(df["date"].dt.date.unique())
    sel_date = ctrl1.selectbox(
        "📅 Select Date",
        available_dates,
        format_func=lambda d: d.strftime("%d %B %Y, %A"),
        index=0,
    )
    traffic_label = ctrl2.selectbox("🚦 Traffic Slot", list(TRAFFIC_FACTORS.keys()), index=1)
    with ctrl3:
        st.markdown("")
        st.markdown("")
        run_btn = st.button("⚡ Optimize Route", use_container_width=True)

    # ── Cost Parameters ──────────────────────────────────────────────────────
    with st.expander("⚙️ Cost Parameters", expanded=False):
        p1, p2, p3, p4 = st.columns(4)
        driver_cost = p1.number_input("Driver Cost (BDT/hr)", value=float(DRIVER_COST_PER_HOUR), step=10.0)
        fuel_cost   = p2.number_input("Fuel Cost (BDT/hr)",   value=float(FUEL_COST_PER_HOUR),   step=10.0)
        avg_speed   = p3.number_input("Avg Speed (km/h)",      value=float(AVG_SPEED_KMPH),       step=1.0)
        truck_cap   = p4.number_input("Truck Capacity (m³)",   value=float(TRUCK_CAPACITY_M3),    step=0.5)
        import vehicle_routing as vr
        vr.DRIVER_COST_PER_HOUR = driver_cost
        vr.FUEL_COST_PER_HOUR   = fuel_cost
        vr.AVG_SPEED_KMPH       = avg_speed
        vr.TRUCK_CAPACITY_M3    = truck_cap

    # ── Day snapshot ─────────────────────────────────────────────────────────
    df_day = df[df["date"].dt.date == sel_date].copy()
    tf     = TRAFFIC_FACTORS[traffic_label]

    ds1, ds2, ds3, ds4 = st.columns(4)
    ds1.markdown(f"""<div class="kpi"><div class="kpi-lbl">Deliveries</div><div class="kpi-val">{len(df_day)}</div><div class="kpi-sub">stops for this day</div></div>""", unsafe_allow_html=True)
    ds2.markdown(f"""<div class="kpi"><div class="kpi-lbl">Total m³</div><div class="kpi-val">{df_day['qty_m3'].sum():,.1f}</div><div class="kpi-sub">concrete volume</div></div>""", unsafe_allow_html=True)
    ds3.markdown(f"""<div class="kpi"><div class="kpi-lbl">Traffic Factor</div><div class="kpi-val">{tf:.1f}×</div><div class="kpi-sub">{traffic_label}</div></div>""", unsafe_allow_html=True)
    ds4.markdown(f"""<div class="kpi"><div class="kpi-lbl">Clients</div><div class="kpi-val">{df_day['client_name'].nunique()}</div><div class="kpi-sub">unique destinations</div></div>""", unsafe_allow_html=True)
    st.markdown("")

    if df_day.empty:
        st.warning("No deliveries for this date.")
        return

    # ── Run optimization ──────────────────────────────────────────────────────
    if run_btn or "route_result" not in st.session_state or st.session_state.get("route_date") != str(sel_date):
        with st.spinner("🔄 Optimizing route & fetching road data from OSRM..."):
            result = optimize_day(df_day, traffic_label)
            st.session_state.route_result = result
            st.session_state.route_date   = str(sel_date)

    result = st.session_state.get("route_result")
    if not result:
        st.info("Click **⚡ Optimize Route** to begin.")
        return

    cost = result["cost"]

    # ── KPI cost cards ────────────────────────────────────────────────────────
    st.markdown("### 💰 Cost Breakdown")
    ck1, ck2, ck3, ck4, ck5 = st.columns(5)
    ck1.markdown(f"""<div class="kpi"><div class="kpi-lbl">Total Distance</div><div class="kpi-val">{cost['total_dist_km']}</div><div class="kpi-sub">km (road estimate)</div></div>""", unsafe_allow_html=True)
    ck2.markdown(f"""<div class="kpi"><div class="kpi-lbl">Total Time</div><div class="kpi-val">{cost['total_time_min']:.0f}</div><div class="kpi-sub">minutes incl traffic</div></div>""", unsafe_allow_html=True)
    ck3.markdown(f"""<div class="kpi"><div class="kpi-lbl">Driver Cost</div><div class="kpi-val">৳{cost['driver_cost_bdt']:,.0f}</div><div class="kpi-sub">BDT</div></div>""", unsafe_allow_html=True)
    ck4.markdown(f"""<div class="kpi"><div class="kpi-lbl">Fuel Cost</div><div class="kpi-val">৳{cost['fuel_cost_bdt']:,.0f}</div><div class="kpi-sub">BDT</div></div>""", unsafe_allow_html=True)
    ck5.markdown(f"""<div class="kpi"><div class="kpi-lbl">Total Cost</div><div class="kpi-val">৳{cost['total_cost_bdt']:,.0f}</div><div class="kpi-sub">BDT · {result['n_trucks']} trucks</div></div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Map ───────────────────────────────────────────────────────────────────
    st.markdown("### 🗺️ Optimal Route Map")
    st.caption("Click any marker for delivery details · Numbers show optimized visit order · Dashed line = route path")

    map_html = render_leaflet_map(result, str(sel_date))
    import streamlit.components.v1 as components
    components.html(map_html, height=600, scrolling=False)

    # ── Segment table ─────────────────────────────────────────────────────────
    st.markdown("### 📍 Route Segments")
    segs = pd.DataFrame(cost["segments"])
    segs.columns = ["From", "To", "Distance (km)", "Travel Time (min)", "Cost (BDT)"]
    segs["Cost (BDT)"] = segs["Cost (BDT)"].apply(lambda x: f"৳{x:,.0f}")
    st.dataframe(segs, use_container_width=True, hide_index=True)

    # ── Truck allocation ──────────────────────────────────────────────────────
    st.markdown("### 🚛 Truck Load Allocation")
    for i, truck in enumerate(result["trucks"]):
        truck_vol = sum(s.get("qty_m3", 0) for s in truck)
        color = TRUCK_COLORS[i % len(TRUCK_COLORS)]
        with st.expander(f"🚛 Truck {i+1}  —  {len(truck)} stops  ·  {truck_vol:.2f} m³"):
            tdf = pd.DataFrame(truck)[["client_name","project_address","qty_m3","psi","pump_status"]]
            tdf.columns = ["Client","Address","m³","PSI","Pump"]
            st.dataframe(tdf, use_container_width=True, hide_index=True)

    # ── Traffic comparison ────────────────────────────────────────────────────
    st.markdown("### 🚦 Traffic Scenario Comparison")
    import vehicle_routing as vr
    rows = []
    for label, factor in TRAFFIC_FACTORS.items():
        base_time = cost["total_time_min"] / tf  # remove current factor
        adj_time  = base_time * factor
        adj_cost  = (adj_time / 60) * (driver_cost + fuel_cost) * factor
        rows.append({
            "Slot":              label,
            "Traffic Factor":    f"{factor}×",
            "Est. Time (min)":   f"{adj_time:.0f}",
            "Total Cost (BDT)":  f"৳{adj_cost:,.0f}",
            "Vs Current":        "← selected" if label == traffic_label else ("🟢 cheaper" if adj_cost < cost["total_cost_bdt"] else "🔴 costlier"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── Monthly summary ───────────────────────────────────────────────────────
    st.markdown("### 📅 Monthly Cost Summary (All March 2026)")
    with st.expander("View estimated cost per day across the full month"):
        monthly = []
        for d in sorted(df["date"].dt.date.unique()):
            ddf = df[df["date"].dt.date == d]
            n   = len(ddf)
            # Quick cost estimate without full optimization
            avg_stops_dist = 8.5 * 1.42  # avg 8.5 km per stop × road factor
            est_dist   = n * avg_stops_dist
            est_time   = (est_dist / avg_speed) * 60 * tf
            est_cost   = (est_time / 60) * (driver_cost + fuel_cost) * tf
            monthly.append({
                "Date":         d.strftime("%d %b %Y"),
                "Deliveries":   n,
                "Total m³":     f"{ddf['qty_m3'].sum():,.1f}",
                "Est. Distance": f"{est_dist:.0f} km",
                "Est. Time":    f"{est_time:.0f} min",
                "Est. Cost":    f"৳{est_cost:,.0f}",
            })
        st.dataframe(pd.DataFrame(monthly), use_container_width=True, hide_index=True)
        total_est = sum(
            float(r["Est. Cost"].replace("৳","").replace(",",""))
            for r in monthly
        )
        st.markdown(f"**Estimated total transport cost for March 2026: ৳{total_est:,.0f} BDT**")
