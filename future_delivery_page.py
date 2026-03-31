"""
future_delivery_page.py
Future Truck Delivery Cost Calculator for ARMCL-01 ERP.
Management-facing: input any origin→destination, get full cost estimate + map.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import math
import requests
from datetime import datetime, date, timedelta

# ── Known locations (factory / depots / common destinations) ──────────────────
KNOWN_ORIGINS = {
    "ARMCL-01 Depot — Dhour, Turag":          (23.8490, 90.3580),
    "ARMCL-02 — Keraniganj":                   (23.6820, 90.3570),
    "ARMCL-03 — Narayanganj":                  (23.6238, 90.5000),
    "Central Warehouse — Gazipur":             (23.9990, 90.4150),
    "Chittagong Plant":                        (22.3569, 91.7832),
    "Custom (enter coordinates below)":        None,
}

KNOWN_DESTINATIONS = {
    "Gulshan, Dhaka":                          (23.7934, 90.4130),
    "Dhanmondi, Dhaka":                        (23.7461, 90.3742),
    "Uttara, Dhaka":                           (23.8759, 90.3795),
    "Mirpur, Dhaka":                           (23.8060, 90.3600),
    "Tongi, Gazipur":                          (23.8940, 90.4050),
    "Ashulia, Savar":                          (23.9100, 90.2650),
    "Tejgaon, Dhaka":                          (23.7710, 90.4000),
    "Bashundhara, Dhaka":                      (23.8140, 90.4350),
    "Baridhara, Dhaka":                        (23.7980, 90.4280),
    "Banani, Dhaka":                           (23.7936, 90.4035),
    "Khilkhet, Dhaka":                         (23.8340, 90.4210),
    "Rayer Bazar, Dhaka":                      (23.7470, 90.3610),
    "Bosila, Mohammadpur":                     (23.7198, 90.3503),
    "Narayanganj":                             (23.6238, 90.5000),
    "Keraniganj":                              (23.6820, 90.3570),
    "Manikganj":                               (23.8640, 90.0120),
    "Narsingdi":                               (23.9225, 90.7153),
    "Gazipur Sadar":                           (23.9990, 90.4150),
    "Savar":                                   (23.8560, 90.2660),
    "Custom (enter coordinates below)":        None,
}

TRUCK_TYPES = {
    "Mixer Truck — 6 m³":    {"capacity": 6.0,  "fuel_lph": 14.0, "speed": 28.0, "fixed_cost": 500},
    "Mixer Truck — 8 m³":    {"capacity": 8.0,  "fuel_lph": 16.0, "speed": 26.0, "fixed_cost": 600},
    "Mixer Truck — 10 m³":   {"capacity": 10.0, "fuel_lph": 18.0, "speed": 24.0, "fixed_cost": 700},
    "Pump Truck":             {"capacity": 0.0,  "fuel_lph": 20.0, "speed": 22.0, "fixed_cost": 1200},
    "Flatbed / Material":     {"capacity": 12.0, "fuel_lph": 12.0, "speed": 35.0, "fixed_cost": 400},
}

TRAFFIC_SLOTS = {
    "Early Morning (6–8 AM)":  1.0,
    "Morning Peak (8–10 AM)":  1.6,
    "Mid Morning (10–12 PM)":  1.3,
    "Afternoon (12–3 PM)":     1.2,
    "Evening Peak (3–7 PM)":   1.8,
    "Night (7 PM+)":           1.1,
}

ROAD_FACTOR   = 1.42
FUEL_PRICE_PER_LITRE = 115.0  # BDT per litre (diesel)
DRIVER_RATE   = 180.0         # BDT/hour
LOADING_TIME  = 25            # minutes at plant
UNLOADING_TIME = 20           # minutes at site


def haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2)
    return R * 2 * math.asin(math.sqrt(a))


def get_osrm(coords, timeout=8):
    coord_str = ";".join(f"{lng},{lat}" for lat, lng in coords)
    url = f"http://router.project-osrm.org/route/v1/driving/{coord_str}?overview=full&geometries=geojson&steps=false"
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            geo  = data["routes"][0]["geometry"]["coordinates"]
            dist_m    = data["routes"][0]["distance"]
            dur_s     = data["routes"][0]["duration"]
            return {
                "polyline":   [[p[1], p[0]] for p in geo],
                "dist_km":    round(dist_m / 1000, 2),
                "duration_min": round(dur_s / 60, 1),
            }
    except Exception:
        pass
    return None


def calculate_cost(dist_km, truck_meta, traffic_factor,
                   driver_rate, fuel_price, qty_m3,
                   num_trucks, include_return):
    speed       = truck_meta["speed"]
    fuel_lph    = truck_meta["fuel_lph"]
    fixed       = truck_meta["fixed_cost"]
    total_dist  = dist_km * (2 if include_return else 1)

    # Travel time (hours)
    travel_h    = (total_dist / speed) * traffic_factor

    # Loading + unloading (hours)
    ops_h       = (LOADING_TIME + UNLOADING_TIME) / 60

    total_h     = travel_h + ops_h

    # Individual costs
    driver_cost = driver_rate * total_h * num_trucks
    fuel_litres = fuel_lph * travel_h * num_trucks
    fuel_cost   = fuel_litres * fuel_price
    fixed_cost  = fixed * num_trucks

    total_cost  = driver_cost + fuel_cost + fixed_cost

    # Per m3 cost
    per_m3 = total_cost / qty_m3 if qty_m3 > 0 else 0

    return {
        "total_dist_km":    round(total_dist, 2),
        "travel_h":         round(travel_h, 2),
        "ops_h":            round(ops_h, 2),
        "total_h":          round(total_h, 2),
        "driver_cost":      round(driver_cost, 0),
        "fuel_litres":      round(fuel_litres, 2),
        "fuel_cost":        round(fuel_cost, 0),
        "fixed_cost":       round(fixed_cost, 0),
        "total_cost":       round(total_cost, 0),
        "per_m3_cost":      round(per_m3, 2),
        "num_trucks":       num_trucks,
        "traffic_factor":   traffic_factor,
    }


def build_map_html(origin_lat, origin_lng, origin_name,
                   dest_lat, dest_lng, dest_name,
                   polyline, dist_km, cost_bdt, trucks) -> str:

    poly_js   = json.dumps(polyline if polyline else [])
    origin_js = json.dumps({"lat": origin_lat, "lng": origin_lng, "name": origin_name})
    dest_js   = json.dumps({"lat": dest_lat,   "lng": dest_lng,   "name": dest_name})
    mid_lat   = (origin_lat + dest_lat) / 2
    mid_lng   = (origin_lng + dest_lng) / 2

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#060a10; }}
#map {{ width:100%; height:500px; border-radius:12px; }}
.info-box {{
    background:rgba(13,20,32,0.95); border:1px solid #1e3050;
    border-radius:8px; padding:12px 16px; font-family:'IBM Plex Mono',monospace;
    font-size:12px; color:#e2e8f0; min-width:200px;
}}
.info-title {{ color:#f97316; font-weight:700; font-size:14px; margin-bottom:8px; }}
.info-row {{ display:flex; justify-content:space-between; gap:16px;
              padding:3px 0; border-bottom:1px solid #1e3050; }}
.info-val {{ color:#22d3a0; font-weight:600; }}
.pop {{ font-family:'IBM Plex Mono',monospace; font-size:12px; min-width:180px; }}
.pop-h {{ color:#f97316; font-weight:700; font-size:13px; margin-bottom:4px; }}
</style>
</head>
<body>
<div id="map"></div>
<script>
const origin  = {origin_js};
const dest    = {dest_js};
const poly    = {poly_js};
const dist    = {dist_km};
const cost    = {cost_bdt};
const trucks  = {trucks};

const map = L.map('map', {{ center:[{mid_lat},{mid_lng}], zoom:11 }});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
    attribution:'© OpenStreetMap contributors', maxZoom:19
}}).addTo(map);

// Route line
if (poly.length > 1) {{
    L.polyline(poly, {{ color:'#f97316', weight:4, opacity:0.9, dashArray:'8,5' }}).addTo(map);
}}

// Origin marker (green)
const oIcon = L.divIcon({{
    html:`<div style="background:#22d3a0;color:#060a10;border-radius:50%;width:32px;height:32px;
          display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;
          border:2px solid #fff;box-shadow:0 2px 12px rgba(34,211,160,0.6)">🏭</div>`,
    className:'', iconSize:[32,32], iconAnchor:[16,16], popupAnchor:[0,-16]
}});
L.marker([origin.lat, origin.lng], {{icon: oIcon}})
 .addTo(map)
 .bindPopup(`<div class='pop'><div class='pop-h'>📍 ORIGIN</div>${{origin.name}}</div>`);

// Destination marker (orange)
const dIcon = L.divIcon({{
    html:`<div style="background:#f97316;color:#fff;border-radius:50%;width:32px;height:32px;
          display:flex;align-items:center;justify-content:center;font-weight:800;font-size:15px;
          border:2px solid #fff;box-shadow:0 2px 12px rgba(249,115,22,0.6)">🏗</div>`,
    className:'', iconSize:[32,32], iconAnchor:[16,16], popupAnchor:[0,-16]
}});
L.marker([dest.lat, dest.lng], {{icon: dIcon}})
 .addTo(map)
 .bindPopup(`<div class='pop'><div class='pop-h'>🏗️ DESTINATION</div>${{dest.name}}</div>`);

// Info box
const info = L.control({{position:'topright'}});
info.onAdd = function() {{
    const d = L.DomUtil.create('div','info-box');
    d.innerHTML = `
        <div class='info-title'>📦 Delivery Summary</div>
        <div class='info-row'><span>Distance</span><span class='info-val'>${{dist}} km</span></div>
        <div class='info-row'><span>Est. Cost</span><span class='info-val'>৳${{cost.toLocaleString()}}</span></div>
        <div class='info-row'><span>Trucks</span><span class='info-val'>${{trucks}}</span></div>
    `;
    return d;
}};
info.addTo(map);

// Fit bounds
const pts = [[origin.lat,origin.lng],[dest.lat,dest.lng]];
if (poly.length > 0) poly.forEach(p => pts.push(p));
map.fitBounds(pts, {{padding:[40,40]}});
</script>
</body>
</html>"""


def render_future_delivery_page():
    st.markdown("# 📦 Future Delivery Cost Calculator")
    st.markdown(
        '<div style="color:#64748b;font-size:.82rem;margin-top:-12px;margin-bottom:24px;">'
        'Calculate exact transport cost for any future truck delivery · Management report ready</div>',
        unsafe_allow_html=True
    )

    # ════════════════════════════════════════════════════
    # INPUT FORM
    # ════════════════════════════════════════════════════
    with st.form("delivery_form"):
        st.markdown("### 📍 Route")
        rc1, rc2 = st.columns(2)

        with rc1:
            st.markdown("**Origin (Factory / Depot)**")
            origin_sel = st.selectbox("Select Origin", list(KNOWN_ORIGINS.keys()), index=0)
            if KNOWN_ORIGINS[origin_sel] is None:
                o_lat = st.number_input("Origin Latitude",  value=23.8490, format="%.6f")
                o_lng = st.number_input("Origin Longitude", value=90.3580, format="%.6f")
                origin_name = st.text_input("Origin Name", value="Custom Origin")
            else:
                o_lat, o_lng = KNOWN_ORIGINS[origin_sel]
                origin_name  = origin_sel
                st.caption(f"📌 {o_lat:.4f}°N, {o_lng:.4f}°E")

        with rc2:
            st.markdown("**Destination (Construction Site)**")
            dest_sel = st.selectbox("Select Destination", list(KNOWN_DESTINATIONS.keys()), index=0)
            if KNOWN_DESTINATIONS[dest_sel] is None:
                d_lat = st.number_input("Destination Latitude",  value=23.7934, format="%.6f")
                d_lng = st.number_input("Destination Longitude", value=90.4130, format="%.6f")
                dest_name = st.text_input("Destination Name", value="Custom Destination")
            else:
                d_lat, d_lng = KNOWN_DESTINATIONS[dest_sel]
                dest_name    = dest_sel
                st.caption(f"📌 {d_lat:.4f}°N, {d_lng:.4f}°E")

        st.markdown("### 🚛 Cargo & Truck")
        cc1, cc2, cc3, cc4 = st.columns(4)
        qty_m3      = cc1.number_input("Concrete Volume (m³)", min_value=1.0, value=50.0, step=1.0)
        psi         = cc2.selectbox("PSI Grade", [3000,3500,4000,4350,4500,5000,5800,6000], index=2)
        truck_type  = cc3.selectbox("Truck Type", list(TRUCK_TYPES.keys()), index=1)
        pump_needed = cc4.selectbox("Pump Truck?", ["No", "Yes"])

        st.markdown("### ⏰ Schedule & Traffic")
        sc1, sc2, sc3, sc4 = st.columns(4)
        delivery_date  = sc1.date_input("Delivery Date", value=date.today() + timedelta(days=1))
        traffic_slot   = sc2.selectbox("Traffic Slot", list(TRAFFIC_SLOTS.keys()), index=1)
        include_return = sc3.selectbox("Include Return Trip?", ["Yes", "No"], index=0) == "Yes"
        urgency        = sc4.selectbox("Urgency", ["Standard", "Priority (+20%)", "Emergency (+50%)"])

        st.markdown("### 💰 Cost Parameters")
        cp1, cp2, cp3 = st.columns(3)
        driver_rate  = cp1.number_input("Driver Rate (BDT/hr)", value=180.0, step=10.0)
        fuel_price   = cp2.number_input("Diesel Price (BDT/litre)", value=115.0, step=1.0)
        overhead_pct = cp3.number_input("Overhead / Margin (%)", value=15.0, step=1.0)

        client_name  = st.text_input("Client Name (for report)", placeholder="e.g. Shanta Holdings Ltd")
        notes        = st.text_area("Notes / Special Instructions", height=55, placeholder="e.g. Narrow access road, requires small pump, site contact: 01XXXXXXXXX")

        submitted = st.form_submit_button("⚡ Calculate Cost & Show Route", use_container_width=True)

    if not submitted:
        st.info("Fill in the form above and click **⚡ Calculate Cost & Show Route** to generate the estimate.")
        return

    # ════════════════════════════════════════════════════
    # CALCULATIONS
    # ════════════════════════════════════════════════════
    truck_meta    = TRUCK_TYPES[truck_type]
    traffic_factor= TRAFFIC_SLOTS[traffic_slot]
    urgency_mult  = {"Standard": 1.0, "Priority (+20%)": 1.20, "Emergency (+50%)": 1.50}[urgency]

    # Number of trucks needed
    cap = truck_meta["capacity"]
    num_trucks = math.ceil(qty_m3 / cap) if cap > 0 else 1
    pump_trucks = 1 if pump_needed == "Yes" else 0

    # Straight-line + road distance
    straight_km = haversine(o_lat, o_lng, d_lat, d_lng)
    road_km     = round(straight_km * ROAD_FACTOR, 2)

    # Try OSRM for real road distance
    with st.spinner("🔄 Fetching real road route from OSRM..."):
        osrm = get_osrm([(o_lat, o_lng), (d_lat, d_lng)])

    if osrm:
        actual_dist_km = osrm["dist_km"]
        polyline       = osrm["polyline"]
        osrm_used      = True
    else:
        actual_dist_km = road_km
        polyline       = [[o_lat, o_lng], [d_lat, d_lng]]
        osrm_used      = False

    # Main cost
    cost = calculate_cost(
        actual_dist_km, truck_meta, traffic_factor,
        driver_rate, fuel_price, qty_m3,
        num_trucks, include_return
    )

    # Pump truck cost (if needed)
    pump_cost_bdt = 0
    if pump_needed == "Yes":
        pump_meta = TRUCK_TYPES["Pump Truck"]
        pump_calc = calculate_cost(
            actual_dist_km, pump_meta, traffic_factor,
            driver_rate, fuel_price, 1,
            pump_trucks, include_return
        )
        pump_cost_bdt = pump_calc["total_cost"]

    subtotal   = cost["total_cost"] + pump_cost_bdt
    overhead   = round(subtotal * overhead_pct / 100, 0)
    grand_total= round((subtotal + overhead) * urgency_mult, 0)
    per_m3     = round(grand_total / qty_m3, 2)

    # ════════════════════════════════════════════════════
    # KPI CARDS
    # ════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📊 Cost Summary")

    k1,k2,k3,k4,k5,k6 = st.columns(6)
    cards = [
        ("Route Distance", f"{actual_dist_km} km",       "road distance" + (" (OSRM)" if osrm_used else " (estimated)")),
        ("Travel Time",    f"{cost['total_h']:.1f} hrs",  f"incl {traffic_factor:.1f}× traffic"),
        ("Trucks Needed",  f"{num_trucks}",                f"{truck_type.split('—')[0].strip()}"),
        ("Driver Cost",    f"৳{cost['driver_cost']:,.0f}", "BDT"),
        ("Fuel Cost",      f"৳{cost['fuel_cost']:,.0f}",  f"{cost['fuel_litres']:.1f} litres"),
        ("TOTAL COST",     f"৳{grand_total:,.0f}",         f"৳{per_m3}/m³"),
    ]
    for col, (lbl, val, sub) in zip([k1,k2,k3,k4,k5,k6], cards):
        col.markdown(f"""
        <div class="kpi">
            <div class="kpi-lbl">{lbl}</div>
            <div class="kpi-val" style="font-size:1.6rem">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ════════════════════════════════════════════════════
    # MAP
    # ════════════════════════════════════════════════════
    st.markdown("### 🗺️ Delivery Route Map")
    if not osrm_used:
        st.caption("⚠️ OSRM unavailable — showing straight-line path. Real road distance estimated with 1.42× factor.")
    else:
        st.caption("✅ Real road route from OSRM · OpenStreetMap tiles · No API key required")

    map_html = build_map_html(
        o_lat, o_lng, origin_name,
        d_lat, d_lng, dest_name,
        polyline, actual_dist_km, grand_total, num_trucks
    )
    components.html(map_html, height=520, scrolling=False)

    # ════════════════════════════════════════════════════
    # FULL COST BREAKDOWN TABLE
    # ════════════════════════════════════════════════════
    st.markdown("### 💰 Full Cost Breakdown")
    breakdown = [
        ("🚛 Truck Type",           truck_type,                            ""),
        ("📏 Straight-line Dist",   f"{straight_km:.2f} km",               ""),
        ("🛣️  Road Distance",        f"{actual_dist_km} km",               "OSRM" if osrm_used else "estimated ×1.42"),
        ("↩️  Return Trip",          "Yes" if include_return else "No",    f"Total dist: {cost['total_dist_km']} km"),
        ("⚡ Avg Speed",             f"{truck_meta['speed']} km/h",         "Dhaka urban avg"),
        ("🚦 Traffic Factor",        f"{traffic_factor}×",                  traffic_slot),
        ("⏱️  Travel Time",          f"{cost['travel_h']} hrs",             "including traffic"),
        ("🔧 Load/Unload Time",      f"{LOADING_TIME+UNLOADING_TIME} min",  "25 min load + 20 min unload"),
        ("⌚ Total Time",            f"{cost['total_h']} hrs",              "per truck"),
        ("👷 Driver Cost",           f"৳{cost['driver_cost']:,.0f}",        f"৳{driver_rate}/hr × {num_trucks} truck(s)"),
        ("⛽ Fuel Consumption",      f"{cost['fuel_litres']:.1f} litres",   f"{truck_meta['fuel_lph']} L/hr × {cost['travel_h']} hrs × {num_trucks} truck(s)"),
        ("💧 Fuel Cost",             f"৳{cost['fuel_cost']:,.0f}",          f"৳{fuel_price}/litre"),
        ("🔩 Fixed/Maintenance",     f"৳{cost['fixed_cost']:,.0f}",         f"৳{truck_meta['fixed_cost']} per truck"),
    ]
    if pump_needed == "Yes":
        breakdown.append(("🚿 Pump Truck Cost", f"৳{pump_cost_bdt:,.0f}", "1 pump truck"))

    breakdown += [
        ("📦 Subtotal",              f"৳{subtotal:,.0f}",                  ""),
        ("📋 Overhead / Margin",     f"৳{overhead:,.0f}",                  f"{overhead_pct}%"),
        ("🚨 Urgency Multiplier",    f"{urgency_mult}×",                    urgency),
        ("✅ GRAND TOTAL",           f"৳{grand_total:,.0f}",                f"৳{per_m3}/m³"),
    ]

    df_break = pd.DataFrame(breakdown, columns=["Item", "Value", "Note"])
    st.dataframe(df_break, use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════
    # ALL-TRAFFIC COMPARISON
    # ════════════════════════════════════════════════════
    st.markdown("### 🚦 Cost Across All Traffic Scenarios")
    traffic_rows = []
    for slot, tf in TRAFFIC_SLOTS.items():
        c = calculate_cost(actual_dist_km, truck_meta, tf,
                           driver_rate, fuel_price, qty_m3, num_trucks, include_return)
        sub  = c["total_cost"] + pump_cost_bdt
        oh   = round(sub * overhead_pct / 100, 0)
        tot  = round((sub + oh) * urgency_mult, 0)
        saving = grand_total - tot
        traffic_rows.append({
            "Time Slot":         slot,
            "Traffic Factor":    f"{tf}×",
            "Travel Time":       f"{c['total_h']:.1f} hrs",
            "Driver Cost":       f"৳{c['driver_cost']:,.0f}",
            "Fuel Cost":         f"৳{c['fuel_cost']:,.0f}",
            "Total Cost":        f"৳{tot:,.0f}",
            "vs Selected Slot":  f"৳{saving:,.0f} {'✅ cheaper' if saving > 0 else ('🔴 costlier' if saving < 0 else '← selected')}",
        })
    st.dataframe(pd.DataFrame(traffic_rows), use_container_width=True, hide_index=True)

    # ════════════════════════════════════════════════════
    # MANAGEMENT REPORT CARD
    # ════════════════════════════════════════════════════
    st.markdown("### 📄 Management Report")

    best_slot  = min(TRAFFIC_SLOTS, key=lambda s: TRAFFIC_SLOTS[s])
    best_tf    = TRAFFIC_SLOTS[best_slot]
    best_c     = calculate_cost(actual_dist_km, truck_meta, best_tf,
                                driver_rate, fuel_price, qty_m3, num_trucks, include_return)
    best_sub   = best_c["total_cost"] + pump_cost_bdt
    best_tot   = round((best_sub + best_sub * overhead_pct / 100) * urgency_mult, 0)
    potential_saving = grand_total - best_tot

    report_html = f"""
<div style="background:#0d1420;border:1px solid #1e3050;border-radius:14px;padding:28px 32px;font-family:'IBM Plex Mono',monospace;color:#e2e8f0;max-width:900px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;padding-bottom:16px;border-bottom:1px solid #1e3050;">
    <div>
      <div style="font-family:'Barlow Condensed',sans-serif;font-size:1.8rem;font-weight:800;color:#f97316;">TRANSPORT COST ESTIMATE</div>
      <div style="color:#64748b;font-size:.78rem;margin-top:2px;">AKIJ READYMIX CONCRETE LTD. · ARMCL-01</div>
    </div>
    <div style="text-align:right;color:#64748b;font-size:.78rem;">
      <div>Date: {datetime.now().strftime('%d %B %Y')}</div>
      <div>Delivery: {delivery_date.strftime('%d %B %Y')}</div>
      <div style="color:#22d3a0;margin-top:4px;">REF: EST-{datetime.now().strftime('%Y%m%d%H%M')}</div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
    <div>
      <div style="color:#64748b;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px;">Route Details</div>
      <div style="padding:12px;background:#111d2e;border-radius:8px;">
        <div style="margin-bottom:6px;"><span style="color:#64748b;">From:</span> <span style="color:#22d3a0;">{origin_name}</span></div>
        <div style="margin-bottom:6px;"><span style="color:#64748b;">To:</span> <span style="color:#22d3a0;">{dest_name}</span></div>
        <div style="margin-bottom:6px;"><span style="color:#64748b;">Distance:</span> {actual_dist_km} km road</div>
        <div><span style="color:#64748b;">Return:</span> {'Yes' if include_return else 'No'}</div>
      </div>
    </div>
    <div>
      <div style="color:#64748b;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px;">Cargo Details</div>
      <div style="padding:12px;background:#111d2e;border-radius:8px;">
        <div style="margin-bottom:6px;"><span style="color:#64748b;">Client:</span> <span style="color:#22d3a0;">{client_name or 'Not specified'}</span></div>
        <div style="margin-bottom:6px;"><span style="color:#64748b;">Volume:</span> {qty_m3} m³ · PSI {psi}</div>
        <div style="margin-bottom:6px;"><span style="color:#64748b;">Truck:</span> {truck_type} × {num_trucks}</div>
        <div><span style="color:#64748b;">Pump:</span> {pump_needed}</div>
      </div>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin-bottom:20px;">
    <div style="background:#162236;border-radius:8px;padding:14px;text-align:center;">
      <div style="color:#64748b;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;">Driver</div>
      <div style="color:#f97316;font-size:1.4rem;font-weight:700;">৳{cost['driver_cost']:,.0f}</div>
    </div>
    <div style="background:#162236;border-radius:8px;padding:14px;text-align:center;">
      <div style="color:#64748b;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;">Fuel</div>
      <div style="color:#38bdf8;font-size:1.4rem;font-weight:700;">৳{cost['fuel_cost']:,.0f}</div>
    </div>
    <div style="background:#162236;border-radius:8px;padding:14px;text-align:center;">
      <div style="color:#64748b;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;">Fixed + OH</div>
      <div style="color:#a78bfa;font-size:1.4rem;font-weight:700;">৳{cost['fixed_cost']+overhead:,.0f}</div>
    </div>
    <div style="background:#1e3050;border:1px solid #f97316;border-radius:8px;padding:14px;text-align:center;">
      <div style="color:#f97316;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;font-weight:700;">TOTAL</div>
      <div style="color:#f97316;font-size:1.6rem;font-weight:800;">৳{grand_total:,.0f}</div>
      <div style="color:#64748b;font-size:.7rem;">৳{per_m3}/m³</div>
    </div>
  </div>

  <div style="background:#111d2e;border-radius:8px;padding:14px;margin-bottom:16px;">
    <div style="color:#fbbf24;font-size:.78rem;font-weight:600;margin-bottom:6px;">💡 Optimization Recommendation</div>
    <div style="color:#94a3b8;font-size:.78rem;line-height:1.7;">
      Dispatching during <strong style="color:#22d3a0;">{best_slot}</strong> instead of <strong style="color:#f97316;">{traffic_slot}</strong>
      would reduce transport cost by <strong style="color:#22d3a0;">৳{potential_saving:,.0f} BDT</strong>
      ({round(potential_saving/grand_total*100,1) if grand_total>0 else 0}% saving) through lower traffic delay on the same route.
    </div>
  </div>

  {'<div style="background:#111d2e;border-radius:8px;padding:12px 14px;margin-bottom:16px;"><div style="color:#64748b;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px;">Notes</div><div style="color:#94a3b8;font-size:.78rem;">' + notes + "</div></div>" if notes else ""}

  <div style="color:#475569;font-size:.68rem;text-align:center;margin-top:4px;">
    Generated by ARMCL-01 ERP · Estimates based on Dhaka road conditions · Subject to variation
  </div>
</div>
"""
    st.markdown(report_html, unsafe_allow_html=True)

    # ════════════════════════════════════════════════════
    # WHAT-IF VOLUME ANALYSIS
    # ════════════════════════════════════════════════════
    st.markdown("### 📈 Volume Sensitivity — How Cost Changes With Volume")
    volumes = [10, 20, 30, 40, 50, 60, 80, 100, 120, 150, 200]
    vol_rows = []
    for v in volumes:
        n = math.ceil(v / cap) if cap > 0 else 1
        c = calculate_cost(actual_dist_km, truck_meta, traffic_factor,
                           driver_rate, fuel_price, v, n, include_return)
        sub = c["total_cost"] + pump_cost_bdt
        tot = round((sub + sub * overhead_pct / 100) * urgency_mult, 0)
        vol_rows.append({
            "Volume (m³)":    v,
            "Trucks":         n,
            "Total Cost":     f"৳{tot:,.0f}",
            "Cost per m³":    f"৳{round(tot/v,2):,.2f}",
            "vs Your Order":  f"৳{tot-grand_total:+,.0f}",
        })
    st.dataframe(pd.DataFrame(vol_rows), use_container_width=True, hide_index=True)
    st.caption("💡 Larger orders spread fixed costs — cost per m³ drops significantly at higher volumes.")
