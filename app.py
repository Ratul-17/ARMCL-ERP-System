"""
ARMCL-01 Daily Production ERP
AKIJ READYMIX CONCRETE LTD. — Dhour Beribadh, Turag, Dhaka
"""
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import os, json, uuid
import sys

# ── Page config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ARMCL-01 Production ERP",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;500;600&family=Barlow+Condensed:wght@400;600;700;800&display=swap');

:root {
    --bg:       #060a10;
    --s1:       #0d1420;
    --s2:       #111d2e;
    --s3:       #162236;
    --accent:   #f97316;
    --accent2:  #fb923c;
    --blue:     #38bdf8;
    --green:    #22d3a0;
    --red:      #f43f5e;
    --yellow:   #fbbf24;
    --text:     #e2e8f0;
    --muted:    #64748b;
    --border:   #1e3050;
}
html, body, [class*="css"] {
    font-family: 'IBM Plex Mono', monospace !important;
    background: var(--bg) !important;
    color: var(--text) !important;
}
.stApp { background: var(--bg) !important; }

section[data-testid="stSidebar"] {
    background: var(--s1) !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] * { color: var(--text) !important; }

h1,h2,h3 { font-family: 'Barlow Condensed', sans-serif !important; letter-spacing: -0.5px; }
h1 { font-size: 2.6rem !important; font-weight: 800 !important; color: var(--accent) !important; }
h2 { font-size: 1.5rem !important; font-weight: 700 !important; color: var(--blue) !important; }
h3 { font-size: 1.15rem !important; font-weight: 600 !important; color: var(--text) !important; }

.kpi { background: var(--s2); border: 1px solid var(--border); border-radius: 10px;
        padding: 18px 22px; position: relative; overflow: hidden; }
.kpi::after { content:''; position:absolute; bottom:0; left:0; right:0; height:3px;
               background: linear-gradient(90deg,var(--accent),var(--blue)); }
.kpi-val  { font-family:'Barlow Condensed',sans-serif; font-size:2.6rem; font-weight:800;
             color:var(--accent); line-height:1; }
.kpi-lbl  { font-size:0.68rem; letter-spacing:.15em; text-transform:uppercase; color:var(--muted); margin-bottom:4px; }
.kpi-sub  { font-size:0.75rem; color:var(--green); margin-top:4px; }

.stButton>button {
    background: linear-gradient(135deg,var(--accent),#ea580c) !important;
    color: white !important; border: none !important; border-radius: 7px !important;
    font-family: 'IBM Plex Mono',monospace !important; font-size:.82rem !important;
    font-weight:500 !important; letter-spacing:.03em;
    transition: all .2s !important;
}
.stButton>button:hover { transform:translateY(-1px) !important; box-shadow:0 8px 24px rgba(249,115,22,.4) !important; }

.stTextInput>div>div>input, .stSelectbox>div>div,
.stDateInput>div>div>input, .stNumberInput>div>div>input,
.stTextArea>div>div>textarea, .stMultiSelect>div>div {
    background: var(--s2) !important; border: 1px solid var(--border) !important;
    border-radius: 7px !important; color: var(--text) !important;
    font-family: 'IBM Plex Mono',monospace !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border-color: var(--accent) !important; box-shadow: 0 0 0 2px rgba(249,115,22,.18) !important;
}
.stDataFrame { border:1px solid var(--border) !important; border-radius:10px; overflow:hidden; }
hr { border-color: var(--border) !important; margin: 20px 0; }

.stSuccess { background:rgba(34,211,160,.08)!important; border:1px solid rgba(34,211,160,.25)!important; border-radius:7px!important; }
.stError   { background:rgba(244,63,94,.08) !important; border:1px solid rgba(244,63,94,.25) !important; border-radius:7px!important; }
.stInfo    { background:rgba(56,189,248,.08)!important; border:1px solid rgba(56,189,248,.25)!important; border-radius:7px!important; }
.stWarning { background:rgba(251,191,36,.08)!important; border:1px solid rgba(251,191,36,.25)!important; border-radius:7px!important; }

.stTabs [data-baseweb="tab-list"] {
    background: var(--s1) !important; border-radius:9px; padding:4px; gap:3px;
    border:1px solid var(--border);
}
.stTabs [data-baseweb="tab"] {
    background:transparent !important; border-radius:6px !important;
    color:var(--muted) !important; font-family:'IBM Plex Mono',monospace !important; font-size:.8rem !important;
}
.stTabs [aria-selected="true"] { background:var(--s3) !important; color:var(--accent) !important; }

.conn-badge   { background:rgba(34,211,160,.12); border:1px solid rgba(34,211,160,.3);
                color:#22d3a0; padding:3px 11px; border-radius:20px; font-size:.7rem; letter-spacing:.08em; }
.disconn-badge { color:var(--muted); font-size:.7rem; }

.day-header { background:var(--s3); border-left:3px solid var(--accent);
               padding:6px 12px; border-radius:0 6px 6px 0; margin:10px 0 6px; font-size:.8rem; letter-spacing:.05em; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────────
PLANTS    = ["Schwing Stetter Plant", "Fujian Xinda Plant"]
PSI_GRADES= [3000, 3500, 3625, 4000, 4060, 4350, 4500, 5000, 5500, 5800, 6000]
DATA_FILE = "armcl_production.csv"
COLS = ["id","date","unit","client_name","project_address","psi","qty_m3","qty_cft","pump_status","notes","created_at"]

# ── Data helpers ──────────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE, dtype=str)
        df["qty_m3"]  = pd.to_numeric(df["qty_m3"],  errors="coerce").fillna(0)
        df["qty_cft"] = pd.to_numeric(df["qty_cft"], errors="coerce").fillna(0)
        df["psi"]     = pd.to_numeric(df["psi"],     errors="coerce").fillna(0).astype(int)
        df["date"]    = pd.to_datetime(df["date"], errors="coerce")
        return df
    return pd.DataFrame(columns=COLS)

def save_data(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False)

def add_record(rec: dict):
    df = load_data()
    new = pd.DataFrame([{c: rec.get(c,"") for c in COLS}])
    df = pd.concat([df, new], ignore_index=True)
    save_data(df)

def update_record(rid: str, updates: dict):
    df = load_data()
    mask = df["id"] == rid
    for k, v in updates.items():
        df.loc[mask, k] = v
    save_data(df)

def delete_record(rid: str):
    df = load_data()
    save_data(df[df["id"] != rid].reset_index(drop=True))

# ── Helper: table renderer (defined here so all pages can use it) ─────────────────
def _show_table(df: pd.DataFrame):
    show = ["id","date","unit","client_name","project_address","psi","qty_m3","qty_cft","pump_status","notes"]
    cols = [c for c in show if c in df.columns]
    renamed = df[cols].rename(columns={
        "id":"ID","date":"Date","unit":"Plant","client_name":"Client",
        "project_address":"Project Address","psi":"PSI",
        "qty_m3":"m³","qty_cft":"CFT","pump_status":"Pump","notes":"Notes"
    })
    st.dataframe(renamed, use_container_width=True, hide_index=True)

# ── Bootstrap: load sample data on first run ──────────────────────────────────────
if not os.path.exists(DATA_FILE):
    sample_path = "march_2026_data.csv"
    if os.path.exists(sample_path):
        raw = pd.read_csv(sample_path)
        raw["id"]         = [str(uuid.uuid4())[:8].upper() for _ in range(len(raw))]
        raw["notes"]      = ""
        raw["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for c in COLS:
            if c not in raw.columns:
                raw[c] = ""
        save_data(raw[COLS])

# ── Session state ─────────────────────────────────────────────────────────────────
if "sheets_connected" not in st.session_state:
    st.session_state.sheets_connected = False
if "sheets_manager" not in st.session_state:
    st.session_state.sheets_manager = None
if "last_sync" not in st.session_state:
    st.session_state.last_sync = None

# ── Sidebar ───────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ ARMCL-01 ERP")
    st.markdown('<div style="color:#64748b;font-size:.7rem;margin-top:-8px;margin-bottom:12px;">AKIJ READYMIX CONCRETE LTD.</div>', unsafe_allow_html=True)
    st.markdown("---")

    page = st.radio("Nav", [
        "📊 Dashboard",
        "➕ Add Production Entry",
        "📋 All Records",
        "🔍 Client Lookup",
        "📅 Daily Summary",
        "🚛 Route Optimizer",
        "📦 Future Delivery Cost",
        "🔗 Google Sheets",
    ], label_visibility="collapsed")

    st.markdown("---")
    df_s = load_data()
    if not df_s.empty:
        st.markdown("**March 2026 Stats**")
        c1, c2 = st.columns(2)
        c1.metric("Entries", len(df_s))
        c2.metric("Total m³", f"{df_s['qty_m3'].sum():,.1f}")
        c3, c4 = st.columns(2)
        c3.metric("Clients", df_s["client_name"].nunique())
        c4.metric("Days", df_s["date"].nunique())

    st.markdown("---")
    if st.session_state.sheets_connected:
        st.markdown('<span class="conn-badge">● SHEETS LIVE</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="disconn-badge">● SHEETS OFFLINE</span>', unsafe_allow_html=True)
    if st.session_state.last_sync:
        st.markdown(f'<div style="color:#475569;font-size:.68rem;margin-top:4px;">Last sync {st.session_state.last_sync}</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.markdown("# ARMCL-01 Production Dashboard")
    st.markdown('<div style="color:#64748b;font-size:.82rem;margin-top:-12px;margin-bottom:20px;">Dhour Beribadh, Turag, Dhaka &nbsp;·&nbsp; March 2026</div>', unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        st.info("No data loaded. Add entries or place `march_2026_data.csv` in the project folder.")
        st.stop()

    total_m3  = df["qty_m3"].sum()
    total_cft = df["qty_cft"].sum()
    total_days = df["date"].nunique()
    avg_day    = total_m3 / total_days if total_days else 0
    pump_yes   = len(df[df["pump_status"].str.lower() == "yes"])
    pump_pct   = pump_yes / len(df) * 100

    k1,k2,k3,k4,k5 = st.columns(5)
    kpis = [
        ("Total Production", f"{total_m3:,.1f}", "m³ concrete"),
        ("Total (CFT)",      f"{total_cft:,.0f}", "cubic feet"),
        ("Avg / Day",        f"{avg_day:,.1f}",   "m³ per day"),
        ("Deliveries",       f"{len(df)}",         f"{df['client_name'].nunique()} clients"),
        ("Pump Used",        f"{pump_pct:.0f}%",   f"{pump_yes} of {len(df)} trips"),
    ]
    for col, (lbl, val, sub) in zip([k1,k2,k3,k4,k5], kpis):
        col.markdown(f"""
        <div class="kpi">
            <div class="kpi-lbl">{lbl}</div>
            <div class="kpi-val">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # Row 1: Daily trend + Plant split
    r1a, r1b = st.columns([3,2])
    with r1a:
        st.markdown("### Daily Production (m³)")
        daily = df.groupby("date")["qty_m3"].sum().reset_index()
        daily_plant = df.groupby(["date","unit"])["qty_m3"].sum().reset_index()
        fig = px.bar(daily_plant, x="date", y="qty_m3", color="unit",
                     color_discrete_map={"Schwing Stetter Plant":"#f97316","Fujian Xinda Plant":"#38bdf8"},
                     barmode="stack", template="plotly_dark", labels={"qty_m3":"m³","date":"Date","unit":"Plant"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=0,r=0,t=10,b=0), legend=dict(orientation="h",y=-0.25),
                          font=dict(family="IBM Plex Mono", color="#94a3b8"),
                          xaxis=dict(gridcolor="#1e3050"), yaxis=dict(gridcolor="#1e3050"))
        st.plotly_chart(fig, use_container_width=True)

    with r1b:
        st.markdown("### Plant Contribution")
        plant_vol = df.groupby("unit")["qty_m3"].sum().reset_index()
        fig2 = px.pie(plant_vol, names="unit", values="qty_m3", hole=0.55, template="plotly_dark",
                      color_discrete_sequence=["#f97316","#38bdf8"])
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=0,r=0,t=10,b=0),
                           font=dict(family="IBM Plex Mono", color="#94a3b8"),
                           legend=dict(orientation="v", x=1, y=0.5))
        fig2.update_traces(textfont_size=11)
        st.plotly_chart(fig2, use_container_width=True)

    # Row 2: PSI distribution + Top clients
    r2a, r2b = st.columns([2,3])
    with r2a:
        st.markdown("### Production by PSI Grade")
        psi_vol = df.groupby("psi")["qty_m3"].sum().reset_index().sort_values("psi")
        psi_vol["psi"] = psi_vol["psi"].astype(str)
        fig3 = px.bar(psi_vol, x="qty_m3", y="psi", orientation="h", template="plotly_dark",
                      labels={"qty_m3":"m³","psi":"PSI Grade"},
                      color="qty_m3", color_continuous_scale=["#1e3050","#f97316"])
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0,r=0,t=10,b=0), coloraxis_showscale=False,
                           font=dict(family="IBM Plex Mono", color="#94a3b8"),
                           yaxis=dict(gridcolor="#1e3050"), xaxis=dict(gridcolor="#1e3050"))
        st.plotly_chart(fig3, use_container_width=True)

    with r2b:
        st.markdown("### Top 12 Clients by Volume")
        top_clients = df.groupby("client_name")["qty_m3"].sum().sort_values(ascending=False).head(12).reset_index()
        fig4 = px.bar(top_clients, x="client_name", y="qty_m3", template="plotly_dark",
                      labels={"qty_m3":"m³","client_name":"Client"},
                      color="qty_m3", color_continuous_scale=["#1e3050","#22d3a0"])
        fig4.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(l=0,r=0,t=10,b=0), coloraxis_showscale=False,
                           font=dict(family="IBM Plex Mono", color="#94a3b8"),
                           xaxis=dict(tickangle=-35, gridcolor="#1e3050"), yaxis=dict(gridcolor="#1e3050"))
        st.plotly_chart(fig4, use_container_width=True)

    # Recent entries table
    st.markdown("### Recent Entries")
    recent = df.sort_values("date", ascending=False).head(10)
    _show_table(recent)

# ════════════════════════════════════════════════════════════════════════════════
#  ADD PRODUCTION ENTRY
# ════════════════════════════════════════════════════════════════════════════════
elif page == "➕ Add Production Entry":
    st.markdown("# Add Production Entry")
    st.markdown('<div style="color:#64748b;font-size:.82rem;margin-top:-12px;margin-bottom:20px;">ARMCL-01 · Daily Production Log</div>', unsafe_allow_html=True)

    with st.form("add_form", clear_on_submit=True):
        st.markdown("#### Delivery Details")
        c1, c2, c3 = st.columns(3)
        entry_date   = c1.date_input("Date *", value=date.today())
        unit         = c2.selectbox("Plant / Unit *", PLANTS)
        psi          = c3.selectbox("PSI Grade *", PSI_GRADES, index=3)

        st.markdown("#### Client & Site")
        c4, c5 = st.columns(2)
        client_name     = c4.text_input("Client Name *", placeholder="e.g. Shanta Holdings Ltd")
        project_address = c5.text_input("Project Address *", placeholder="e.g. Dhanmondi, Dhaka")

        st.markdown("#### Production")
        c6, c7, c8 = st.columns(3)
        qty_m3      = c6.number_input("Quantity (m³) *", min_value=0.0, step=0.5, format="%.2f")
        qty_cft_val = round(qty_m3 * 35.315, 2)
        c7.metric("Auto (CFT)", f"{qty_cft_val:,.2f}")
        pump_status = c8.selectbox("Pump Used?", ["Yes", "No"])

        notes = st.text_area("Remarks / Notes", placeholder="Any additional notes", height=60)
        submitted = st.form_submit_button("💾 Save Entry", use_container_width=True)

    if submitted:
        if not client_name or qty_m3 <= 0:
            st.error("Client Name and Quantity (>0) are required.")
        else:
            rec = {
                "id":              str(uuid.uuid4())[:8].upper(),
                "date":            str(entry_date),
                "unit":            unit,
                "client_name":     client_name.strip(),
                "project_address": project_address.strip(),
                "psi":             int(psi),
                "qty_m3":          float(qty_m3),
                "qty_cft":         float(qty_cft_val),
                "pump_status":     pump_status,
                "notes":           notes,
                "created_at":      datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            add_record(rec)
            # Sync to sheets if connected
            if st.session_state.sheets_connected and st.session_state.sheets_manager:
                try:
                    st.session_state.sheets_manager.push_data(load_data())
                    st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")
                    st.success(f"✅ Saved & synced to Google Sheets! ID: `{rec['id']}`")
                except Exception as e:
                    st.warning(f"Saved locally. Sheets sync failed: {e}")
            else:
                st.success(f"✅ Entry saved! ID: `{rec['id']}` — {qty_m3} m³ / {qty_cft_val} CFT for {client_name}")

# ════════════════════════════════════════════════════════════════════════════════
#  ALL RECORDS
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📋 All Records":
    st.markdown("# All Production Records")

    df = load_data()
    if df.empty:
        st.info("No records found.")
        st.stop()

    with st.expander("🔎 Filters", expanded=True):
        fc1, fc2, fc3, fc4 = st.columns(4)
        search       = fc1.text_input("Search client / address", "")
        plant_filter = fc2.multiselect("Plant", PLANTS, default=PLANTS)
        psi_filter   = fc3.multiselect("PSI Grade", sorted(df["psi"].unique().tolist()), default=sorted(df["psi"].unique().tolist()))
        pump_filter  = fc4.multiselect("Pump Used", ["Yes","No"], default=["Yes","No"])

    fdf = df.copy()
    if search:
        fdf = fdf[fdf["client_name"].str.contains(search, case=False, na=False) |
                  fdf["project_address"].str.contains(search, case=False, na=False)]
    if plant_filter: fdf = fdf[fdf["unit"].isin(plant_filter)]
    if psi_filter:   fdf = fdf[fdf["psi"].isin(psi_filter)]
    if pump_filter:  fdf = fdf[fdf["pump_status"].isin(pump_filter)]

    fdf_sorted = fdf.sort_values("date", ascending=False)

    st.markdown(f'<div style="color:#64748b;font-size:.78rem;margin-bottom:10px;">{len(fdf_sorted)} records · {fdf_sorted["qty_m3"].sum():,.2f} m³ total</div>', unsafe_allow_html=True)

    bc1, bc2, bc3 = st.columns([1,1,6])
    csv_bytes = fdf_sorted.to_csv(index=False).encode()
    bc1.download_button("⬇ CSV", csv_bytes, "armcl_march2026.csv", "text/csv", use_container_width=True)
    if st.session_state.sheets_connected and st.session_state.sheets_manager:
        if bc2.button("☁ Sync", use_container_width=True):
            st.session_state.sheets_manager.push_data(load_data())
            st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")
            st.success("Synced!")

    _show_table(fdf_sorted)

    # Edit / Delete
    st.markdown("---")
    st.markdown("### Edit a Record")
    ids = fdf_sorted["id"].tolist()
    if ids:
        sel = st.selectbox("Select Record ID", ids)
        row = fdf_sorted[fdf_sorted["id"] == sel].iloc[0]
        with st.form("edit_form"):
            ec1,ec2,ec3 = st.columns(3)
            new_qty    = ec1.number_input("Qty (m³)", value=float(row["qty_m3"]), step=0.5, format="%.2f")
            new_pump   = ec2.selectbox("Pump Used?", ["Yes","No"], index=0 if row["pump_status"]=="Yes" else 1)
            new_psi    = ec3.selectbox("PSI", PSI_GRADES, index=PSI_GRADES.index(int(row["psi"])) if int(row["psi"]) in PSI_GRADES else 3)
            new_notes  = st.text_area("Notes", value=row.get("notes","") or "")
            eu, ed = st.columns(2)
            upd = eu.form_submit_button("✏️ Update", use_container_width=True)
            dlt = ed.form_submit_button("🗑 Delete", use_container_width=True)
        if upd:
            update_record(sel, {"qty_m3": new_qty, "qty_cft": round(new_qty*35.315,2), "pump_status": new_pump, "psi": new_psi, "notes": new_notes})
            if st.session_state.sheets_connected and st.session_state.sheets_manager:
                st.session_state.sheets_manager.push_data(load_data())
                st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")
            st.success(f"Updated `{sel}`"); st.rerun()
        if dlt:
            delete_record(sel)
            st.warning(f"Deleted `{sel}`"); st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
#  CLIENT LOOKUP
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Client Lookup":
    st.markdown("# Client Lookup")
    st.markdown('<div style="color:#64748b;font-size:.82rem;margin-top:-12px;margin-bottom:20px;">Delivery history per client</div>', unsafe_allow_html=True)

    df = load_data()
    if df.empty: st.info("No data."); st.stop()

    clients = sorted(df["client_name"].unique().tolist())
    sel_client = st.selectbox("Select Client", clients)
    cdf = df[df["client_name"] == sel_client].sort_values("date")

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Deliveries",    len(cdf))
    m2.metric("Total m³",     f"{cdf['qty_m3'].sum():,.2f}")
    m3.metric("Total CFT",    f"{cdf['qty_cft'].sum():,.0f}")
    m4.metric("Pump Used",    f"{(cdf['pump_status'].str.lower()=='yes').sum()}/{len(cdf)}")

    if len(cdf) > 1:
        fig = px.bar(cdf, x="date", y="qty_m3", color="unit",
                     color_discrete_map={"Schwing Stetter Plant":"#f97316","Fujian Xinda Plant":"#38bdf8"},
                     template="plotly_dark", labels={"qty_m3":"m³","date":"Date"})
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=0,r=0,t=10,b=0), font=dict(family="IBM Plex Mono",color="#94a3b8"),
                          xaxis=dict(gridcolor="#1e3050"), yaxis=dict(gridcolor="#1e3050"))
        st.plotly_chart(fig, use_container_width=True)

    _show_table(cdf)

# ════════════════════════════════════════════════════════════════════════════════
#  DAILY SUMMARY
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📅 Daily Summary":
    st.markdown("# Daily Summary")
    st.markdown('<div style="color:#64748b;font-size:.82rem;margin-top:-12px;margin-bottom:20px;">All deliveries grouped by date</div>', unsafe_allow_html=True)

    df = load_data()
    if df.empty: st.info("No data."); st.stop()

    available_dates = sorted(df["date"].dropna().dt.date.unique(), reverse=True)
    sel_date = st.selectbox("Select Date", available_dates, format_func=lambda d: d.strftime("%d %B %Y, %A"))

    ddf = df[df["date"].notna() & (df["date"].dt.date == sel_date)].sort_values("unit")
    total_day = ddf["qty_m3"].sum()
    ss_vol = ddf[ddf["unit"]=="Schwing Stetter Plant"]["qty_m3"].sum()
    fx_vol = ddf[ddf["unit"]=="Fujian Xinda Plant"]["qty_m3"].sum()

    dm1,dm2,dm3,dm4 = st.columns(4)
    dm1.metric("Total (m³)",      f"{total_day:,.2f}")
    dm2.metric("Schwing Stetter", f"{ss_vol:,.2f} m³")
    dm3.metric("Fujian Xinda",    f"{fx_vol:,.2f} m³")
    dm4.metric("Deliveries",      len(ddf))

    st.markdown("---")
    for plant in PLANTS:
        pdf = ddf[ddf["unit"] == plant]
        if pdf.empty: continue
        st.markdown(f'<div class="day-header">🔶 {plant} — {pdf["qty_m3"].sum():,.2f} m³ / {pdf["qty_cft"].sum():,.0f} CFT</div>', unsafe_allow_html=True)
        _show_table(pdf)

# ════════════════════════════════════════════════════════════════════════════════
#  GOOGLE SHEETS
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🔗 Google Sheets":
    st.markdown("# Google Sheets Sync")

    t1, t2, t3 = st.tabs(["🔐 Connect", "☁ Push Data", "⬇ Pull Data"])

    with t1:
        st.markdown("### Connect via Service Account")
        st.info("""
**Setup (one-time):**
1. [Google Cloud Console](https://console.cloud.google.com/) → New Project
2. Enable **Google Sheets API** + **Google Drive API**
3. **IAM & Admin** → Service Accounts → Create → Download **JSON key**
4. Open your Google Sheet → Share with the service account email as **Editor**
        """)
        cred_file = st.file_uploader("Upload credentials JSON", type=["json"])
        sheet_url  = st.text_input("Google Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/...")
        ws_name    = st.text_input("Sheet Tab Name", value=" March-2026")

        if st.button("🔗 Connect"):
            if cred_file and sheet_url:
                try:
                    import tempfile
                    from sheets_manager import GoogleSheetsManager
                    cred_data = json.load(cred_file)
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        json.dump(cred_data, f); tmp = f.name
                    sid = sheet_url.strip()
                    if "spreadsheets/d/" in sid:
                        sid = sid.split("spreadsheets/d/")[1].split("/")[0]
                    sm = GoogleSheetsManager(tmp, sid, ws_name)
                    sm.ensure_worksheet()
                    st.session_state.sheets_manager = sm
                    st.session_state.sheets_connected = True
                    os.unlink(tmp)
                    st.success("✅ Connected to Google Sheets!")
                except Exception as e:
                    st.error(f"Failed: {e}")
            else:
                st.warning("Upload credentials and provide the Sheet URL.")

    with t2:
        if not st.session_state.sheets_connected:
            st.warning("Connect first.")
        else:
            df = load_data()
            st.markdown(f"**{len(df)} records** ready to push.")
            st.dataframe(df.head(5), use_container_width=True)
            if st.button("☁ Push All to Google Sheets", use_container_width=True):
                try:
                    st.session_state.sheets_manager.push_data(df)
                    st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")
                    st.success(f"✅ {len(df)} records pushed!")
                except Exception as e:
                    st.error(f"Push failed: {e}")

    with t3:
        if not st.session_state.sheets_connected:
            st.warning("Connect first.")
        else:
            st.warning("⚠ This will overwrite local data with Google Sheets data.")
            if st.button("⬇ Pull from Google Sheets", use_container_width=True):
                try:
                    pulled = st.session_state.sheets_manager.pull_data()
                    save_data(pulled)
                    st.session_state.last_sync = datetime.now().strftime("%H:%M:%S")
                    st.success(f"✅ Pulled {len(pulled)} records!")
                    st.dataframe(pulled.head(10), use_container_width=True)
                except Exception as e:
                    st.error(f"Pull failed: {e}")

# ════════════════════════════════════════════════════════════════════════════════
#  ROUTE OPTIMIZER
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🚛 Route Optimizer":
    try:
        from routing_page import render_routing_page
        render_routing_page()
    except ImportError as e:
        st.error(f"Routing module not found: {e}. Make sure `routing_page.py` and `vehicle_routing.py` are in the same folder.")
    except Exception as e:
        st.error(f"Routing error: {e}")
        import traceback
        st.code(traceback.format_exc())

# ════════════════════════════════════════════════════════════════════════════════
#  FUTURE DELIVERY COST
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📦 Future Delivery Cost":
    try:
        from future_delivery_page import render_future_delivery_page
        render_future_delivery_page()
    except ImportError as e:
        st.error(f"Module not found: {e}. Make sure `future_delivery_page.py` is in the same folder.")
    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())


