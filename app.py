"""
Neete AI Gateway — Observability Dashboard
Langfuse-style | NEETE Brand | Black & Orange
"""

import streamlit as st
import httpx
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Neete AI Gateway",
    page_icon="https://img.icons8.com/fluency/48/artificial-intelligence.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

GATEWAY_URL = st.secrets["GATEWAY_URL"]
GATEWAY_KEY = st.secrets["GATEWAY_KEY"]
HEADERS     = {"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"}

# ─────────────────────────────────────────────
# GLOBAL CSS — NEETE Design System
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Base ── */
* { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
.stApp { background-color: #080808 !important; color: #E8E8E8; }
.main .block-container { padding: 24px 32px 48px !important; max-width: 1400px; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0C0C0C !important;
    border-right: 1px solid #1E1E1E !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
[data-testid="stSidebarNav"] { display: none; }

/* ── Sidebar logo strip ── */
.neete-logo-strip {
    background: linear-gradient(135deg, #0F0F0F 0%, #141414 100%);
    border-bottom: 1px solid #1E1E1E;
    padding: 20px 20px 16px;
    margin-bottom: 4px;
}
.neete-wordmark {
    display: flex;
    align-items: center;
    gap: 12px;
}
.neete-monogram {
    width: 36px; height: 36px;
    background: #FF6B00;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 900; color: #000;
    letter-spacing: -0.02em;
    flex-shrink: 0;
}
.neete-brand-text { line-height: 1; }
.neete-brand-name {
    font-size: 1.05rem; font-weight: 800;
    color: #FFFFFF; letter-spacing: 0.06em;
}
.neete-brand-sub {
    font-size: 0.6rem; font-weight: 500;
    color: #444; letter-spacing: 0.14em;
    text-transform: uppercase; margin-top: 2px;
}

/* ── Nav items ── */
.nav-item {
    display: block;
    padding: 9px 16px;
    margin: 2px 10px;
    border-radius: 7px;
    color: #666 !important;
    font-size: 0.82rem;
    font-weight: 500;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.15s ease;
    letter-spacing: 0.01em;
}
.nav-item:hover { background: #161616; color: #CCC !important; }
.nav-item.active {
    background: #1A0D00;
    color: #FF6B00 !important;
    font-weight: 600;
    border-left: 3px solid #FF6B00;
    padding-left: 13px;
}
.nav-section-label {
    padding: 12px 20px 4px;
    font-size: 0.62rem;
    font-weight: 600;
    color: #333;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #111111 !important;
    border: 1px solid #1E1E1E !important;
    border-top: 2px solid #FF6B00 !important;
    border-radius: 10px !important;
    padding: 18px 20px !important;
    transition: border-color 0.2s;
}
[data-testid="metric-container"]:hover { border-color: #FF8C00 !important; }
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricLabel"] {
    color: #555 !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── Section headers ── */
.section-title {
    font-size: 0.75rem;
    font-weight: 600;
    color: #555;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #1A1A1A;
}

/* ── Cards ── */
.card {
    background: #111111;
    border: 1px solid #1E1E1E;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
}
.card-accent { border-left: 3px solid #FF6B00; }
.card-green  { border-left: 3px solid #00C853; }
.card-red    { border-left: 3px solid #FF3D00; }

.stat-card { background:#111; border:1px solid #1E1E1E; border-left:3px solid #FF6B00;
             border-radius:10px; padding:16px 18px; margin:5px 0; }
.stat-label { color:#444; font-size:0.68rem; text-transform:uppercase;
              letter-spacing:0.1em; margin:0; font-weight:600; }
.stat-value { color:#FF6B00; font-size:1.5rem; font-weight:700; margin:6px 0 0 0; }

/* ── Status badges ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.badge-live  { background: #0A2A14; color: #00C853; border: 1px solid #00C853; }
.badge-down  { background: #2A0A0A; color: #FF3D00; border: 1px solid #FF3D00; }
.badge-warn  { background: #2A1A00; color: #FF6B00; border: 1px solid #FF6B00; }
.badge-groq  { background: #1A0D00; color: #FF6B00; border: 1px solid #FF6B00; }
.badge-nim   { background: #001A0A; color: #00C853; border: 1px solid #00C853; }

.status-live { color: #00C853; font-weight: 600; font-size: 0.78rem; }
.status-down { color: #FF3D00; font-weight: 600; font-size: 0.78rem; }
.status-warn { color: #FF6B00; font-weight: 600; font-size: 0.78rem; }

/* ── Divider ── */
hr { border: none !important; border-top: 1px solid #161616 !important; margin: 20px 0 !important; }

/* ── Hide Streamlit sidebar collapse icon text leak ── */
[data-testid="collapsedControl"] { display: none !important; }
button[kind="headerNoPadding"] { display: none !important; }
.st-emotion-cache-czk5ss { display: none !important; }
section[data-testid="stSidebarCollapsedControl"] { display: none !important; }
/* Hide the keyboard_double_arrow icon name that leaks as text */
[data-testid="stSidebarCollapseButton"] { display: none !important; }
[data-testid="stSidebarUserContent"] > div:first-child button { display: none !important; }
/* Hide Streamlit top toolbar icons that show as text */
.st-emotion-cache-1avcm0n { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }

/* ── Buttons ── */
.stButton > button {
    background: #FF6B00 !important;
    color: #000 !important;
    border: none !important;
    border-radius: 7px !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.04em !important;
    padding: 8px 18px !important;
    transition: background 0.15s !important;
}
.stButton > button:hover { background: #FF8534 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1E1E1E !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
.stDataFrame thead tr th {
    background: #111 !important;
    color: #555 !important;
    font-size: 0.7rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    border-bottom: 1px solid #1E1E1E !important;
}

/* ── Inputs ── */
.stTextInput > div > div, .stTextArea > div > div {
    background: #111 !important;
    border-color: #222 !important;
    border-radius: 7px !important;
    color: #DDD !important;
}
.stSelectbox > div > div {
    background: #111 !important;
    border-color: #222 !important;
    border-radius: 7px !important;
}
.stSlider > div { padding: 4px 0 !important; }
.stNumberInput > div > div { background: #111 !important; border-color: #222 !important; }

/* ── Radio (nav) ── */
[data-testid="stRadio"] label {
    font-size: 0.82rem !important;
    color: #555 !important;
    padding: 6px 10px !important;
}
[data-testid="stRadio"] label:hover { color: #CCC !important; }

/* ── Toggle ── */
[data-testid="stToggle"] { margin: 4px 0 !important; }

/* ── Chat message boxes ── */
.chat-user {
    background: #141414; border: 1px solid #222;
    border-left: 3px solid #444; border-radius: 8px;
    padding: 12px 16px; margin: 8px 0;
}
.chat-assistant {
    background: #0F0F0F; border: 1px solid #1E1E1E;
    border-left: 3px solid #FF6B00; border-radius: 8px;
    padding: 12px 16px; margin: 8px 0;
}
.chat-role {
    font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 8px;
}
.chat-content { font-size: 0.87rem; line-height: 1.65; white-space: pre-wrap; }

/* ── Page title ── */
.page-header {
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #161616;
}
.page-title {
    font-size: 1.35rem; font-weight: 700; color: #FFF;
    letter-spacing: -0.01em; margin: 0;
}
.page-subtitle {
    font-size: 0.78rem; color: #444; margin-top: 4px;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #FF6B00 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0C0C0C; }
::-webkit-scrollbar-thumb { background: #2A2A2A; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #FF6B00; }

/* ── Alert/info boxes ── */
[data-testid="stAlert"] { border-radius: 8px !important; border-left-width: 3px !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# AUTH — NEETE branded login
# ─────────────────────────────────────────────
def check_auth():
    if not st.session_state.get("authenticated"):
        st.markdown("""
        <style>
        .stApp { background: #080808 !important; }
        .main .block-container { max-width: 420px !important; padding-top: 80px !important; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align:center; margin-bottom:40px;'>
            <div style='display:inline-flex; align-items:center; gap:14px; margin-bottom:16px;'>
                <div style='
                    width:52px; height:52px;
                    background:#FF6B00; border-radius:14px;
                    display:flex; align-items:center; justify-content:center;
                    font-size:1.5rem; font-weight:900; color:#000;
                    box-shadow:0 0 30px rgba(255,107,0,0.3);
                '>N</div>
                <div style='text-align:left;'>
                    <div style='font-size:1.4rem; font-weight:800; color:#FFF; letter-spacing:0.08em;'>NEETE</div>
                    <div style='font-size:0.62rem; color:#444; letter-spacing:0.18em; text-transform:uppercase;'>AI Gateway Platform</div>
                </div>
            </div>
            <div style='color:#333; font-size:0.78rem;'>Neete IT Division — Internal Access Only</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.markdown("<p style='color:#555; font-size:0.78rem; margin-bottom:6px; font-weight:600; letter-spacing:0.05em;'>ACCESS PASSWORD</p>", unsafe_allow_html=True)
            pwd = st.text_input("", type="password", placeholder="Enter your password", label_visibility="collapsed")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            if st.form_submit_button("Sign In", use_container_width=True):
                if pwd == st.secrets["DASHBOARD_PASSWORD"]:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password. Contact Neete IT Division.")

        st.markdown("""
        <div style='text-align:center; margin-top:32px; color:#222; font-size:0.68rem;'>
            Neete IT Division &nbsp;·&nbsp; Funcool Manufacturing
        </div>
        """, unsafe_allow_html=True)
        st.stop()

check_auth()


# ─────────────────────────────────────────────
# DATA FETCHERS — tiered TTL caching
# ─────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_health() -> bool:
    try:
        return httpx.get(f"{GATEWAY_URL}/health", timeout=5).status_code == 200
    except:
        return False

@st.cache_data(ttl=300)
def fetch_models() -> list:
    try:
        r = httpx.get(f"{GATEWAY_URL}/v1/models", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            d = r.json()
            return d.get("models", d.get("data", []))
        return []
    except:
        return []

@st.cache_data(ttl=15)
def fetch_quota() -> dict:
    """
    Fetch quota and build TWO lookup maps:
      - by provider_model_id  (e.g. "llama-3.1-8b-instant")
      - by canonical_name     (e.g. "llama-3.1-8b")  ← built from models list
    """
    try:
        r = httpx.get(f"{GATEWAY_URL}/v1/quota", headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return {}
        raw   = r.json()
        items = raw.get("quota", [])

        total_req_used  = sum(q["requests"]["used"]  for q in items)
        total_tok_used  = sum(q["tokens"]["used"]    for q in items)
        total_tok_limit = sum(q["tokens"]["limit"]   for q in items)

        # Keyed by provider_model_id (what quota returns)
        model_usage_by_provider_id = {}
        for q in items:
            model_usage_by_provider_id[q["model"]] = {
                "tokens":   q["tokens"],
                "requests": q["requests"],
                "provider": q["provider"],
            }

        # Build canonical → provider_model_id map from /v1/models
        try:
            mr = httpx.get(f"{GATEWAY_URL}/v1/models", headers=HEADERS, timeout=10)
            all_models = mr.json().get("models", []) if mr.status_code == 200 else []
        except:
            all_models = []

        # Build canonical_name → usage lookup
        model_usage_by_canonical = {}
        for m in all_models:
            canonical = m.get("canonical_name", "")
            prov_list = m.get("providers", [])
            if not prov_list:
                continue
            provider_model_id = prov_list[0].get("provider_model_id", "")
            # Try exact match first, then partial match
            usage = (
                model_usage_by_provider_id.get(provider_model_id) or
                model_usage_by_provider_id.get(canonical) or
                next((v for k, v in model_usage_by_provider_id.items()
                      if canonical in k or k in canonical), None)
            )
            if usage:
                model_usage_by_canonical[canonical] = usage

        # Provider breakdown
        prov_map = {}
        for q in items:
            p = q["provider"]
            prov_map[p] = prov_map.get(p, 0) + q["requests"]["used"]

        return {
            "requests_today":     total_req_used,
            "tokens_today":       total_tok_used,
            "tokens_limit":       total_tok_limit,
            "model_usage":        model_usage_by_canonical,
            "provider_breakdown": prov_map,
            "raw":                items,
        }
    except Exception as e:
        return {}

@st.cache_data(ttl=30)
def fetch_keys() -> list:
    try:
        r = httpx.get(f"{GATEWAY_URL}/v1/keys", headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        d = r.json()
        # /v1/keys returns {"description":..., "keys":[...]} not a plain list
        if isinstance(d, dict):
            return d.get("keys", [])
        return d if isinstance(d, list) else []
    except:
        return []

@st.cache_data(ttl=15)
def fetch_alerts() -> list:
    try:
        r = httpx.get(f"{GATEWAY_URL}/v1/alerts", headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return []
        d = r.json()
        # /v1/alerts returns {"alerts":[...]} or a plain list
        if isinstance(d, dict):
            return d.get("alerts", [])
        return d if isinstance(d, list) else []
    except:
        return []

@st.cache_data(ttl=15)
def fetch_model_stats() -> list:
    """Fetch per-model token stats from /v1/model-stats (our independent tracker)."""
    try:
        r = httpx.get(f"{GATEWAY_URL}/v1/model-stats", headers=HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("models", [])
        return []
    except:
        return []

def auto_refresh(seconds: int = 30):
    st.markdown(
        f"<script>setTimeout(()=>window.location.reload(),{seconds*1000});</script>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# SIDEBAR — NEETE branded
# ─────────────────────────────────────────────
with st.sidebar:
    # ── Logo strip ────────────────────────────
    is_live = fetch_health()
    st.markdown(f"""
    <div class='neete-logo-strip'>
        <div class='neete-wordmark'>
            <div class='neete-monogram'>N</div>
            <div class='neete-brand-text'>
                <div class='neete-brand-name'>NEETE</div>
                <div class='neete-brand-sub'>AI Gateway Platform</div>
            </div>
        </div>
        <div style='margin-top:12px; display:flex; align-items:center; justify-content:space-between;'>
            <span class='badge {'badge-live' if is_live else 'badge-down'}'>
                {'● LIVE' if is_live else '● DOWN'}
            </span>
            <span style='color:#2A2A2A; font-size:0.68rem;'>
                {datetime.now().strftime('%d %b, %I:%M %p')}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Navigation ────────────────────────────
    st.markdown("<div class='nav-section-label'>OBSERVE</div>", unsafe_allow_html=True)
    page = st.radio("", [
        "Dashboard",
        "Model Analytics",
        "Usage Trends",
        "Alerts",
        "Test LLM",
    ], label_visibility="collapsed")

    # ── Actions ───────────────────────────────
    st.markdown("<div class='nav-section-label'>ACTIONS</div>", unsafe_allow_html=True)
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    auto = st.toggle("Auto Refresh (30s)", value=True)
    if auto:
        auto_refresh(30)

    # ── Footer ────────────────────────────────
    st.markdown("""
    <div style='position:fixed; bottom:0; left:0; width:260px;
                background:#0C0C0C; border-top:1px solid #161616;
                padding:12px 20px;'>
        <div style='font-size:0.65rem; color:#2A2A2A; font-weight:500;'>
            Neete IT Division &nbsp;·&nbsp; Funcool
        </div>
        <div style='font-size:0.6rem; color:#1E1E1E; margin-top:2px;'>
            Powered by Groq + NVIDIA NIM
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE 1 — DASHBOARD (Langfuse-style unified)
# ─────────────────────────────────────────────
if page == "Dashboard":
    # ── Fetch all data ────────────────────────────────────────────
    models = fetch_models()
    quota  = fetch_quota()
    keys   = fetch_keys()
    alerts = fetch_alerts()
    stats  = fetch_model_stats()   # independent per-model tracker

    is_live = fetch_health()

    # ── Derived values ────────────────────────────────────────────
    tok_today    = sum(s["today"]["total_tokens"]    for s in stats) if stats else quota.get("tokens_today", 0)
    req_today    = sum(s["today"]["requests"]        for s in stats) if stats else quota.get("requests_today", 0)
    tok_alltime  = sum(s["all_time"]["total_tokens"] for s in stats) if stats else 0
    req_alltime  = sum(s["all_time"]["requests"]     for s in stats) if stats else 0
    active_now   = sum(s.get("this_minute_requests", 0) for s in stats) if stats else 0
    active_mdls  = sum(1 for s in stats if s["today"]["requests"] > 0) if stats else 0
    # Use quota limit if available; estimate from raw items as fallback
    _raw_limit = quota.get("tokens_limit", 0)
    if not _raw_limit and quota.get("raw"):
        _raw_limit = sum(q.get("tokens", {}).get("limit", 0) for q in quota.get("raw", []))
    tok_limit = _raw_limit if _raw_limit > 0 else max(tok_today * 10, 500_000)
    tok_pct   = min(100, tok_today / tok_limit * 100) if tok_limit else 0

    groq_models_list = [m for m in models if any(
        p.get("provider", "").lower() == "groq" for p in m.get("providers", [])
    )]
    nim_models_list  = [m for m in models if m not in groq_models_list]

    # ── Page header ───────────────────────────────────────────────
    st.markdown(f"""
    <div class='page-header'>
        <div style='display:flex; align-items:center; justify-content:space-between;'>
            <div>
                <p class='page-title'>Dashboard</p>
                <p class='page-subtitle'>
                    {datetime.now().strftime('%d %b %Y, %I:%M:%S %p IST')}
                    &nbsp;·&nbsp; Groq: {len(groq_models_list)} models
                    &nbsp;·&nbsp; NIM: {len(nim_models_list)} models
                </p>
            </div>
            <span class='badge {'badge-live' if is_live else 'badge-down'}'>
                {'● GATEWAY LIVE' if is_live else '● GATEWAY DOWN'}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row ───────────────────────────────────────────────────
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Tokens Today",     f"{tok_today:,}")
    k2.metric("Requests Today",   f"{req_today:,}")
    k3.metric("Active Models",    f"{active_mdls}")
    k4.metric("All-Time Tokens",  f"{tok_alltime:,}")
    k5.metric("All-Time Requests",f"{req_alltime:,}")
    k6.metric("Req This Minute",  f"{active_now}")

    st.divider()

    # ── Row 1: Quota gauge + Provider pie + Key pool ──────────────
    r1a, r1b, r1c = st.columns([2, 2, 1])

    with r1a:
        st.markdown("<p class='section-title'>Daily Quota Usage</p>", unsafe_allow_html=True)
        color_g = "#00C853" if tok_pct < 60 else "#FF6B00" if tok_pct < 85 else "#FF3D00"
        fig_g = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=tok_pct,
            number={"suffix": "%", "font": {"color": color_g, "size": 32}},
            delta={"reference": 85, "increasing": {"color": "#FF3D00"}, "decreasing": {"color": "#00C853"}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"color": "#555"}},
                "bar":  {"color": color_g, "thickness": 0.22},
                "bgcolor": "#1A1A1A", "bordercolor": "#222",
                "steps": [
                    {"range": [0,  60], "color": "#0D1A0D"},
                    {"range": [60, 85], "color": "#1A0D00"},
                    {"range": [85,100], "color": "#1A0000"},
                ],
                "threshold": {"line": {"color": "#FF3D00", "width": 2}, "thickness": 0.75, "value": 85},
            },
        ))
        fig_g.update_layout(
            paper_bgcolor="#141414", font=dict(color="white"),
            height=210, margin=dict(t=10, b=0, l=20, r=20),
        )
        st.plotly_chart(fig_g, use_container_width=True)
        ga, gb, gc = st.columns(3)
        ga.metric("Used",      f"{tok_today:,}")
        gb.metric("Remaining", f"{max(0, tok_limit - tok_today):,}")
        gc.metric("Limit",     f"{tok_limit:,}")

    with r1b:
        st.markdown("<p class='section-title'>Provider Split — Models</p>", unsafe_allow_html=True)
        fig_p = go.Figure(go.Pie(
            labels=["Groq", "NVIDIA NIM"],
            values=[len(groq_models_list), len(nim_models_list)],
            hole=0.62,
            marker=dict(colors=["#FF6B00", "#E65100"], line=dict(color="#0A0A0A", width=2)),
            textinfo="label+value",
            textfont=dict(color="white", size=12),
            hovertemplate="%{label}: %{value} models<extra></extra>",
        ))
        fig_p.update_layout(
            paper_bgcolor="#141414", font=dict(color="white"),
            showlegend=False, height=240,
            margin=dict(t=10, b=10, l=10, r=10),
            annotations=[dict(
                text=f"<b>{len(models)}</b><br><span style='font-size:9px'>Models</span>",
                x=0.5, y=0.5, font=dict(size=20, color="#FF6B00"), showarrow=False,
            )],
        )
        st.plotly_chart(fig_p, use_container_width=True)

    with r1c:
        st.markdown("<p class='section-title'>Key Pool</p>", unsafe_allow_html=True)
        active_keys    = [k for k in keys if isinstance(k, dict) and not k.get("is_exhausted") and k.get("is_active")]
        exhausted_keys = [k for k in keys if isinstance(k, dict) and k.get("is_exhausted")]
        st.markdown(
            f"<div class='stat-card' style='margin-bottom:8px;'>"
            f"<p class='stat-label'>Active Keys</p>"
            f"<p class='stat-value'>{len(active_keys)}</p></div>"
            f"<div class='stat-card' style='border-left-color:#555;'>"
            f"<p class='stat-label'>Exhausted</p>"
            f"<p class='stat-value' style='color:#888;'>{len(exhausted_keys)}</p></div>",
            unsafe_allow_html=True,
        )
        if alerts:
            st.markdown(
                f"<div class='stat-card' style='border-left-color:#FF3D00; margin-top:8px;'>"
                f"<p class='stat-label'>Alerts</p>"
                f"<p class='stat-value' style='color:#FF3D00;'>{len(alerts)}</p></div>",
                unsafe_allow_html=True,
            )

    st.divider()

    # ── Row 2: Per-model usage table ──────────────────────────────
    st.markdown("<p class='section-title'>Model Usage — Today vs All Time</p>", unsafe_allow_html=True)

    quota_by_model = quota.get("model_usage", {})

    # Build a flexible lookup: try exact match, then strip prefix, then partial
    def _find_quota(model_id: str) -> dict:
        if not quota_by_model:
            return {}
        # exact
        if model_id in quota_by_model:
            return quota_by_model[model_id]
        # strip org prefix e.g. "openai/gpt-oss-120b" → "gpt-oss-120b"
        short = model_id.split("/")[-1]
        if short in quota_by_model:
            return quota_by_model[short]
        # partial substring match
        for k, v in quota_by_model.items():
            if short in k or k in model_id:
                return v
        return {}

    if stats:
        tbl_rows = []
        for s in stats:
            mid      = s["model_id"]
            prov     = s.get("provider", "").upper()
            t_today  = s["today"]["total_tokens"]
            r_today  = s["today"]["requests"]
            t_all    = s["all_time"]["total_tokens"]
            r_all    = s["all_time"]["requests"]
            this_min = s.get("this_minute_requests", 0)
            q        = _find_quota(mid)
            remaining = q.get("tokens", {}).get("remaining", 0) if q else 0
            tbl_rows.append({
                "Model":          mid,
                "Provider":       prov,
                "Tokens Today":   t_today,
                "Req Today":      r_today,
                "Remaining":      remaining or 0,
                "All-Time Tokens":t_all,
                "All-Time Req":   r_all,
                "Req/Min":        this_min,
            })
        tbl_rows.sort(key=lambda x: -x["Tokens Today"])

        st.dataframe(
            pd.DataFrame(tbl_rows),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Tokens Today":    st.column_config.NumberColumn(format="%d"),
                "All-Time Tokens": st.column_config.NumberColumn(format="%d"),
                "Req Today":       st.column_config.NumberColumn(format="%d"),
                "All-Time Req":    st.column_config.NumberColumn(format="%d"),
                "Remaining":       st.column_config.NumberColumn(format="%d"),
                "Req/Min":         st.column_config.NumberColumn(format="%d"),
            },
        )
    else:
        # Fallback: show quota-based data from provider
        raw_quota = quota.get("raw", [])
        if raw_quota:
            q_rows = [{
                "Model":     q["model"],
                "Provider":  q["provider"].upper(),
                "Tokens Used": q["tokens"]["used"],
                "Tokens Remaining": q["tokens"]["remaining"],
                "Req Used":  q["requests"]["used"],
                "Req Remaining": q["requests"]["remaining"],
            } for q in raw_quota]
            st.dataframe(pd.DataFrame(q_rows), use_container_width=True, hide_index=True)
        else:
            st.info("No usage data yet — make a test call from Test LLM to start tracking.")

    st.divider()

    # ── Row 3: Token charts ───────────────────────────────────────
    ch1, ch2 = st.columns(2)

    with ch1:
        st.markdown("<p class='section-title'>Tokens Used Today — By Model</p>", unsafe_allow_html=True)
        chart_today = [s for s in stats if s["today"]["total_tokens"] > 0] if stats else []
        if chart_today:
            chart_today.sort(key=lambda x: -x["today"]["total_tokens"])
            fig_td = go.Figure(go.Bar(
                x=[s["model_id"] for s in chart_today],
                y=[s["today"]["total_tokens"] for s in chart_today],
                marker_color="#FF6B00",
                text=[f"{s['today']['total_tokens']:,}" for s in chart_today],
                textposition="outside",
            ))
            fig_td.update_layout(
                paper_bgcolor="#0A0A0A", plot_bgcolor="#0A0A0A",
                font=dict(color="#CCC", size=10),
                xaxis=dict(tickangle=-40, gridcolor="#1A1A1A"),
                yaxis=dict(gridcolor="#1A1A1A"),
                margin=dict(t=20, b=80, l=50, r=10), height=300,
            )
            st.plotly_chart(fig_td, use_container_width=True)
        else:
            st.caption("No token usage recorded today yet.")

    with ch2:
        st.markdown("<p class='section-title'>All-Time Token Usage — Since Day One</p>", unsafe_allow_html=True)
        if stats:
            chart_all = sorted(stats, key=lambda x: -x["all_time"]["total_tokens"])
            fig_al = go.Figure(go.Bar(
                x=[s["model_id"] for s in chart_all],
                y=[s["all_time"]["total_tokens"] for s in chart_all],
                marker_color="#E65100",
                text=[f"{s['all_time']['total_tokens']:,}" for s in chart_all],
                textposition="outside",
            ))
            fig_al.update_layout(
                paper_bgcolor="#0A0A0A", plot_bgcolor="#0A0A0A",
                font=dict(color="#CCC", size=10),
                xaxis=dict(tickangle=-40, gridcolor="#1A1A1A"),
                yaxis=dict(gridcolor="#1A1A1A"),
                margin=dict(t=20, b=80, l=50, r=10), height=300,
            )
            st.plotly_chart(fig_al, use_container_width=True)
        else:
            st.caption("No all-time data yet.")

    st.divider()

    # ── Row 4: Live rate + Recent alerts ─────────────────────────
    live_col, alert_col = st.columns([1, 1])

    with live_col:
        st.markdown("<p class='section-title'>Live — Requests This Minute</p>", unsafe_allow_html=True)
        active_right_now = [(s["model_id"], s.get("this_minute_requests", 0))
                            for s in stats if s.get("this_minute_requests", 0) > 0] if stats else []
        if active_right_now:
            for mid, cnt in sorted(active_right_now, key=lambda x: -x[1]):
                st.markdown(
                    f"<div style='background:#141414;border:1px solid #2A2A2A;"
                    f"border-left:3px solid #FF6B00;border-radius:6px;"
                    f"padding:9px 14px;margin:4px 0;"
                    f"display:flex;justify-content:space-between;align-items:center;'>"
                    f"<span style='color:#CCC;font-size:0.83rem;'>{mid}</span>"
                    f"<span style='color:#FF6B00;font-weight:700;font-size:0.83rem;'>{cnt} req/min</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div style='color:#555;font-size:0.83rem;padding:20px 0;'>System idle — no requests this minute.</div>",
                unsafe_allow_html=True,
            )

    with alert_col:
        st.markdown("<p class='section-title'>Recent Alerts</p>", unsafe_allow_html=True)
        recent_alerts = alerts[:5] if alerts else []
        if recent_alerts:
            for a in recent_alerts:
                if isinstance(a, dict):
                    pct    = a.get("alert_pct", 0)
                    color_a = "#FF3D00" if pct >= 90 else "#FF6B00" if pct >= 75 else "#FFC107"
                    st.markdown(
                        f"<div style='background:#141414;border:1px solid #2A2A2A;"
                        f"border-left:3px solid {color_a};border-radius:6px;"
                        f"padding:9px 14px;margin:4px 0;'>"
                        f"<span style='color:{color_a};font-size:0.78rem;font-weight:700;'>{pct}% USED</span>"
                        f"<span style='color:#777;font-size:0.75rem;margin-left:8px;'>{a.get('model_id','')}</span>"
                        f"<div style='color:#555;font-size:0.7rem;margin-top:2px;'>{a.get('created_at','')[:16]}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
        else:
            st.markdown(
                "<div style='color:#555;font-size:0.83rem;padding:20px 0;'>No alerts fired yet.</div>",
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────
# PAGE 3 — MODEL ANALYTICS
# ─────────────────────────────────────────────
elif page == "Model Analytics":
    st.markdown("## Model Analytics")
    st.caption("Per-model token utilization and quota remaining")

    models = fetch_models()
    quota  = fetch_quota()

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        provider_filter = st.selectbox("Filter by Provider", ["All", "Groq", "NVIDIA NIM"])

    # Search Model adapts based on Provider filter
    def get_provider_label(m):
        prov_list = m.get("providers", [])
        provider  = prov_list[0].get("provider", "nim").upper() if prov_list else "NIM"
        return "Groq" if provider == "GROQ" else "NVIDIA NIM"

    if provider_filter == "All":
        filtered_for_search = models
    else:
        filtered_for_search = [m for m in models if get_provider_label(m) == provider_filter]

    filtered_model_ids = sorted([m.get("canonical_name","") for m in filtered_for_search if m.get("canonical_name")])

    with col2:
        search_model = st.selectbox(
            "Search Model",
            options=["All Models"] + filtered_model_ids,
            index=0,
        )
    with col3:
        sort_by = st.selectbox("Sort by", ["Usage", "Available Keys"])

    st.divider()

    model_usage  = quota.get("model_usage", {})
    # Also pull our independent tracker stats and key by model_id
    tracker_stats = fetch_model_stats()
    tracker_by_id = {s["model_id"]: s for s in tracker_stats}

    def _match_usage(canonical, prov_model_id):
        """Try multiple key forms to find quota usage."""
        for key in [canonical, prov_model_id, prov_model_id.split("/")[-1], canonical.split("/")[-1]]:
            if key and key in model_usage:
                return model_usage[key]
        # partial match
        for k, v in model_usage.items():
            if canonical in k or k in canonical or prov_model_id in k:
                return v
        return {}

    def _match_tracker(canonical, prov_model_id):
        """Try multiple key forms to find tracker stats."""
        for key in [prov_model_id, canonical, prov_model_id.split("/")[-1], canonical.split("/")[-1]]:
            if key and key in tracker_by_id:
                return tracker_by_id[key]
        return {}

    rows = []
    for m in models:
        mid      = m.get("canonical_name", "")
        prov_list= m.get("providers", [])
        provider = prov_list[0].get("provider", "nim").upper() if prov_list else "NIM"
        prov_label = "Groq" if provider == "GROQ" else "NVIDIA NIM"

        if provider_filter != "All" and prov_label != provider_filter:
            continue
        if search_model != "All Models" and mid != search_model:
            continue

        provider_model_id = prov_list[0].get("provider_model_id", mid) if prov_list else mid
        usage_entry = _match_usage(mid, provider_model_id)
        tracker_entry = _match_tracker(mid, provider_model_id)

        tok_data  = usage_entry.get("tokens", {})
        # Prefer our independent tracker for "used" — more accurate
        used      = tracker_entry.get("today", {}).get("total_tokens", 0) or tok_data.get("used", 0)
        limit     = tok_data.get("limit", 100_000) or 100_000
        remaining = tok_data.get("remaining", max(0, limit - used))
        pct       = round(used / limit * 100, 1) if limit else 0.0
        req_day   = prov_list[0].get("req_per_day", 0) if prov_list else 0

        req_data  = usage_entry.get("requests", {}) if usage_entry else {}
        req_used  = tracker_entry.get("today", {}).get("requests", 0) or req_data.get("used", 0)
        req_limit = req_data.get("limit", req_day) or req_day

        rows.append({
            "Model":           mid,
            "Provider":        prov_label,
            "Tokens Used":     used,
            "Tokens Remaining":remaining,
            "Token Limit":     limit,
            "Usage %":         round(pct, 1),
            "Requests Today":  req_used,
            "Req Limit/Day":   req_limit,
            "Available Keys":  m.get("available_keys", 0),
            "Status":          m.get("status", "unknown"),
        })

    if sort_by == "Available Keys":
        rows = sorted(rows, key=lambda x: x["Available Keys"], reverse=True)
    else:  # Usage
        rows = sorted(rows, key=lambda x: x["Usage %"], reverse=True)

    df = pd.DataFrame(rows)

    if not df.empty:
        total    = len(df)
        avail    = len(df[df["Status"] == "available"])
        no_usage = len(df[df["Tokens Used"] == 0])

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Filtered Models", total)
        c2.metric("Available", avail)
        c3.metric("Not Used Today", no_usage)
        c4.metric("In Use", total - no_usage)

        st.divider()

        # Top models by usage
        st.markdown("#### Token Usage by Model")
        top_used = df[df["Tokens Used"] > 0].nlargest(15, "Tokens Used")

        if not top_used.empty:
            fig = go.Figure(go.Bar(
                x=top_used["Tokens Used"],
                y=top_used["Model"],
                orientation="h",
                marker=dict(
                    color=top_used["Usage %"],
                    colorscale=[[0,"#003300"],[0.6,"#FF6B00"],[1,"#FF3D00"]],
                    showscale=True,
                    colorbar=dict(title="Usage %", tickfont=dict(color="white"), title_font=dict(color="white")),
                ),
                text=[f"{v:,}" for v in top_used["Tokens Used"]],
                textposition="outside",
                textfont=dict(color="#AAA", size=10),
                hovertemplate="<b>%{y}</b><br>%{x:,} tokens<extra></extra>",
            ))
            fig.update_layout(
                paper_bgcolor="#141414",
                plot_bgcolor="#141414",
                font=dict(color="white"),
                xaxis=dict(showgrid=True, gridcolor="#222", title="Tokens Used Today"),
                yaxis=dict(showgrid=False, autorange="reversed"),
                margin=dict(t=10, b=40, l=10, r=80),
                height=max(300, len(top_used) * 32),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No token usage recorded yet. Make LLM calls to see data here.")

        st.divider()
        st.markdown("#### All Models")
        st.dataframe(
            df[[
                "Model", "Provider",
                "Tokens Used", "Tokens Remaining", "Token Limit",
                "Usage %",
                "Requests Today", "Req Limit/Day",
                "Available Keys", "Status"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Usage %": st.column_config.ProgressColumn(
                    "Usage %", min_value=0, max_value=100, format="%.1f%%"
                ),
                "Tokens Used":      st.column_config.NumberColumn("Tokens Used Today", format="%d"),
                "Tokens Remaining": st.column_config.NumberColumn("Remaining",         format="%d"),
                "Token Limit":      st.column_config.NumberColumn("Daily Limit",        format="%d"),
                "Requests Today":   st.column_config.NumberColumn("Req Today",          format="%d"),
                "Req Limit/Day":    st.column_config.NumberColumn("Req Limit",          format="%d"),
                "Available Keys":   st.column_config.NumberColumn("Keys",               format="%d"),
            }
        )
    else:
        st.warning("No models match the selected filters.")


# ─────────────────────────────────────────────
# PAGE 3 — USAGE TRENDS
# ─────────────────────────────────────────────
elif page == "Usage Trends":
    st.markdown("## Usage Trends")
    st.caption("Token and request trends — resets midnight IST")

    quota = fetch_quota()

    st.markdown("#### Hourly Token Consumption")
    hourly = quota.get("hourly_usage", [])
    hours  = [f"{h:02d}:00" for h in range(24)]
    values = [0] * 24

    if hourly:
        for h in hourly:
            idx = int(h.get("hour", 0))
            if 0 <= idx < 24:
                values[idx] = h.get("tokens", 0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours, y=values,
        fill="tozeroy",
        fillcolor="rgba(255,107,0,0.12)",
        line=dict(color="#FF6B00", width=2),
        mode="lines+markers",
        marker=dict(color="#FF6B00", size=5),
        hovertemplate="%{x}: %{y:,} tokens<extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="#141414",
        plot_bgcolor="#141414",
        font=dict(color="white"),
        xaxis=dict(showgrid=True, gridcolor="#1A1A1A", title="Hour (IST)"),
        yaxis=dict(showgrid=True, gridcolor="#1A1A1A", title="Tokens"),
        margin=dict(t=10, b=40, l=10, r=10),
        height=300,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Requests by Provider")
        prov_data = quota.get("provider_breakdown", {"groq": quota.get("requests_today", 0), "nim": 0})
        fig2 = go.Figure(go.Bar(
            x=list(prov_data.keys()),
            y=list(prov_data.values()),
            marker_color=["#FF6B00","#CC4400"],
            text=list(prov_data.values()),
            textposition="outside",
            textfont=dict(color="white", size=12),
            hovertemplate="%{x}: %{y:,} requests<extra></extra>",
        ))
        fig2.update_layout(
            paper_bgcolor="#141414", plot_bgcolor="#141414",
            font=dict(color="white"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1A1A1A"),
            margin=dict(t=20, b=20, l=10, r=10),
            height=260,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("#### Today's Summary")
        used     = quota.get("tokens_today", 0)
        requests = quota.get("requests_today", 0)
        avg_tok  = round(used / requests, 1) if requests > 0 else 0

        now     = datetime.now()
        eod     = now.replace(hour=23, minute=59, second=59)
        hrs_left, rem = divmod(int((eod - now).total_seconds()) // 60, 60)

        metrics = [
            ("Total Requests", f"{requests:,}"),
            ("Total Tokens", f"{used:,}"),
            ("Avg Tokens / Request", f"{avg_tok:,}"),
            ("Resets In (IST)", f"{hrs_left}h {rem}m"),
            ("Est. Savings vs GPT-4", f"~Rs {used * 0.00016:.2f}"),
        ]
        for label, value in metrics:
            st.markdown(f"""
            <div class="stat-card">
                <p class="stat-label">{label}</p>
                <p class="stat-value">{value}</p>
            </div>
            """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE 4 — ALERTS
# ─────────────────────────────────────────────
elif page == "Alerts":
    st.markdown("## Alert Center")

    alerts = fetch_alerts()
    keys   = fetch_keys()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Alerts", len(alerts))
    c2.metric("Critical", len([a for a in alerts if a.get("severity") == "critical"]))
    c3.metric("Warning",  len([a for a in alerts if a.get("severity") != "critical"]))

    st.divider()

    st.markdown("#### Threshold Configuration")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("""<div class="stat-card">
            <p class="stat-label">Warning Threshold</p>
            <p class="stat-value">75%</p>
            <p style='color:#555;font-size:0.72rem;margin:0;'>Switches to least-used key</p>
        </div>""", unsafe_allow_html=True)
    with t2:
        st.markdown("""<div class="stat-card">
            <p class="stat-label">Critical Threshold</p>
            <p class="stat-value" style='color:#FF3D00;'>90%</p>
            <p style='color:#555;font-size:0.72rem;margin:0;'>Email alert triggered</p>
        </div>""", unsafe_allow_html=True)
    with t3:
        st.markdown("""<div class="stat-card">
            <p class="stat-label">Daily Reset</p>
            <p class="stat-value" style='color:#00C853;'>00:00 IST</p>
            <p style='color:#555;font-size:0.72rem;margin:0;'>All counters reset</p>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("#### Alert History")

    if alerts:
        alert_df = pd.DataFrame(alerts)
        st.dataframe(alert_df, use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div class="stat-card" style="text-align:center; padding:30px;">
            <p style='color:#00C853; font-size:1rem; font-weight:600; margin:0;'>All Clear</p>
            <p style='color:#555; font-size:0.8rem; margin:4px 0 0;'>No alerts — all keys within quota</p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE 5 — TEST LLM
# ─────────────────────────────────────────────
elif page == "Test LLM":
    st.markdown("## Live LLM Test Console")
    st.caption("Test any model through the Neete AI Gateway in real-time")

    # ── Model config row ──────────────────────────────────────────
    all_models = fetch_models()

    # Build provider → canonical_name list from live DB
    groq_models = sorted([
        m["canonical_name"] for m in all_models
        if any(p.get("provider", "").lower() == "groq"
               for p in m.get("providers", []))
    ])
    nim_models = sorted([
        m["canonical_name"] for m in all_models
        if any(p.get("provider", "").lower() in ("nim", "nvidia", "nvidia nim")
               for p in m.get("providers", []))
    ])

    # Fallback if gateway unreachable — known working models
    if not groq_models:
        groq_models = ["llama-3.1-8b", "llama-3.3-70b", "llama-4-scout", "allam-2-7b"]
    if not nim_models:
        nim_models = [
            "nemotron-mini-4b-instruct", "gemma-3n-e4b-it", "gemma-2-2b-it",
            "llama-4-maverick-17b-128e-instruct", "mixtral-8x7b-instruct-v0.1",
            "llama-3.2-1b-instruct", "llama-3.2-3b-instruct", "nemotron-super",
        ]

    cfg1, cfg2, cfg3, cfg4 = st.columns([2, 3, 1, 1])

    with cfg1:
        provider_choice = st.selectbox(
            "Provider",
            ["Groq", "NVIDIA NIM"],
            help="Groq: stable, fast. NIM: larger models, may vary."
        )

    model_pool = groq_models if provider_choice == "Groq" else nim_models

    with cfg2:
        selected_model = st.selectbox(
            f"Model  ({len(model_pool)} available from gateway)",
            options=model_pool,
        )

    with cfg3:
        temperature = st.slider("Temp", 0.0, 2.0, 0.7, 0.1)

    with cfg4:
        max_tokens = st.number_input("Max Tokens", 64, 4096, 512)

    system_prompt = st.text_input(
        "System Prompt (optional)",
        placeholder="e.g. You are a manufacturing assistant for Funcool.",
    )

    st.divider()

    # ── Session state: conversation history ───────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []   # list of {role, content, meta}
    if "chat_model" not in st.session_state:
        st.session_state.chat_model = selected_model

    # Reset conversation when model changes
    if st.session_state.chat_model != selected_model:
        st.session_state.chat_history = []
        st.session_state.chat_model = selected_model

    # ── Conversation history display ──────────────────────────────
    history_container = st.container()

    with history_container:
        if not st.session_state.chat_history:
            st.markdown(
                "<div style='text-align:center; color:#555; padding:40px 0;'>"
                "No messages yet — start a conversation below."
                "</div>",
                unsafe_allow_html=True,
            )
        else:
            for turn in st.session_state.chat_history:
                role = turn["role"]
                content = turn["content"]
                meta = turn.get("meta", {})

                if role == "user":
                    st.markdown(f"""
                    <div style='background:#1A1A1A; border:1px solid #333; border-left:3px solid #666;
                                border-radius:8px; padding:14px 18px; margin:8px 0; color:#CCC;
                                font-size:0.88rem; line-height:1.6;'>
                        <div style='color:#888; font-size:0.72rem; text-transform:uppercase;
                                    letter-spacing:0.06em; margin-bottom:8px;'>You</div>
                        {content}
                    </div>
                    """, unsafe_allow_html=True)

                elif role == "assistant":
                    meta_line = ""
                    if meta:
                        meta_line = (
                            f"<div style='color:#555; font-size:0.7rem; margin-top:10px;'>"
                            f"Model: {meta.get('model', selected_model)}  |  "
                            f"Provider: {meta.get('provider', '')}  |  "
                            f"Latency: {meta.get('latency_ms', 0):.0f}ms  |  "
                            f"Tokens: {meta.get('total_tokens', 0)}"
                            f"</div>"
                        )
                    st.markdown(f"""
                    <div style='background:#141414; border:1px solid #2A2A2A; border-left:3px solid #FF6B00;
                                border-radius:8px; padding:14px 18px; margin:8px 0; color:#DDD;
                                font-size:0.88rem; line-height:1.6;'>
                        <div style='color:#FF6B00; font-size:0.72rem; text-transform:uppercase;
                                    letter-spacing:0.06em; margin-bottom:8px;'>Gateway Response</div>
                        <div style='white-space:pre-wrap;'>{content}</div>
                        {meta_line}
                    </div>
                    """, unsafe_allow_html=True)

    # ── Input + action buttons ────────────────────────────────────
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    user_input = st.text_area(
        "Your Message",
        placeholder="Enter your message and click Send...",
        height=90,
        key="user_input_box",
        label_visibility="collapsed",
    )

    btn1, btn2, btn3 = st.columns([3, 1, 1])

    with btn1:
        send_clicked = st.button("Send", use_container_width=True)

    with btn2:
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    with btn3:
        # Show cumulative token usage for this session
        session_tokens = sum(
            t.get("meta", {}).get("total_tokens", 0)
            for t in st.session_state.chat_history
            if t["role"] == "assistant"
        )
        st.markdown(
            f"<div style='text-align:center; padding:6px; color:#888; font-size:0.78rem;'>"
            f"Session Tokens<br><span style='color:#FF6B00; font-weight:700;'>{session_tokens:,}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Send logic ────────────────────────────────────────────────
    if send_clicked:
        if not user_input.strip():
            st.warning("Please enter a message.")
        else:
            # Build messages: system prompt + full conversation history + new user message
            messages = []
            if system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt.strip()})
            for turn in st.session_state.chat_history:
                messages.append({"role": turn["role"], "content": turn["content"]})
            messages.append({"role": "user", "content": user_input.strip()})

            # Save user turn immediately
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input.strip(),
                "meta": {},
            })

            with st.spinner(f"Waiting for {selected_model}..."):
                t0 = time.perf_counter()
                try:
                    resp = httpx.post(
                        f"{GATEWAY_URL}/v1/chat",
                        json={
                            "model":       selected_model,
                            "messages":    messages,
                            "temperature": temperature,
                            "max_tokens":  int(max_tokens),
                        },
                        headers=HEADERS,
                        timeout=60,
                    )
                    latency = (time.perf_counter() - t0) * 1000

                    if resp.status_code == 200:
                        data    = resp.json()
                        content = data.get("content") or ""
                        usage   = data.get("usage", {})

                        meta = {
                            "model":             data.get("model", selected_model),
                            "provider":          data.get("provider", provider_choice),
                            "latency_ms":        data.get("latency_ms", latency),
                            "prompt_tokens":     usage.get("prompt_tokens", 0),
                            "completion_tokens": usage.get("completion_tokens", 0),
                            "total_tokens":      usage.get("total_tokens", 0),
                        }

                        # Save assistant turn
                        st.session_state.chat_history.append({
                            "role":    "assistant",
                            "content": content,
                            "meta":    meta,
                        })

                        st.rerun()

                    else:
                        # Remove the user turn we already saved since it failed
                        st.session_state.chat_history.pop()
                        try:
                            err_body = resp.json()
                            err_msg  = err_body.get("detail", resp.text)
                            if isinstance(err_msg, dict):
                                err_msg = err_msg.get("message", str(err_msg))
                        except Exception:
                            err_msg = resp.text
                        st.error(f"Error {resp.status_code}: {err_msg}")

                except httpx.TimeoutException:
                    st.session_state.chat_history.pop()
                    st.error(f"Request timed out after 60s. Model {selected_model} may be overloaded — try Groq models for fastest response.")
                except Exception as e:
                    st.session_state.chat_history.pop()
                    st.error(f"Request failed: {e}")
