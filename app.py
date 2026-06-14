"""
Neete AI Gateway — Observability Dashboard
Industry Standard | Black & Orange
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
    page_title="Neete AI Gateway | Observability",
    page_icon="N",
    layout="wide",
    initial_sidebar_state="expanded",
)

GATEWAY_URL = st.secrets["GATEWAY_URL"]
GATEWAY_KEY = st.secrets["GATEWAY_KEY"]
HEADERS     = {"Authorization": f"Bearer {GATEWAY_KEY}", "Content-Type": "application/json"}

# ─────────────────────────────────────────────
# THEME — Black & Orange
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #0A0A0A; color: #FFFFFF; }

    [data-testid="stSidebar"] {
        background-color: #0F0F0F;
        border-right: 1px solid #FF6B00;
    }

    [data-testid="metric-container"] {
        background: #141414;
        border: 1px solid #2A2A2A;
        border-radius: 8px;
        padding: 16px;
        border-left: 3px solid #FF6B00;
    }
    [data-testid="stMetricValue"] {
        color: #FF6B00 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #888888 !important;
        font-size: 0.78rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    h1, h2, h3, h4 { color: #FFFFFF !important; font-weight: 600 !important; }
    p, span, label { color: #CCCCCC; }
    hr { border-color: #222222 !important; }

    .stat-card {
        background: #141414;
        border: 1px solid #2A2A2A;
        border-left: 3px solid #FF6B00;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 4px 0;
    }
    .stat-label {
        color: #888;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0;
    }
    .stat-value {
        color: #FF6B00;
        font-size: 1.6rem;
        font-weight: 700;
        margin: 4px 0 0 0;
    }

    .status-live   { color: #00C853; font-weight: 600; font-size: 0.8rem; }
    .status-down   { color: #FF3D00; font-weight: 600; font-size: 0.8rem; }
    .status-warn   { color: #FF6B00; font-weight: 600; font-size: 0.8rem; }

    .tag-groq { background:#1A1000; color:#FF6B00; border:1px solid #FF6B00;
                padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; }
    .tag-nim  { background:#001A10; color:#00C853; border:1px solid #00C853;
                padding:2px 8px; border-radius:4px; font-size:0.7rem; font-weight:600; }

    .stButton > button {
        background: #FF6B00 !important;
        color: #000 !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        letter-spacing: 0.04em;
    }
    .stButton > button:hover { background: #FF8C00 !important; }

    [data-testid="stDataFrame"] { border: 1px solid #222; border-radius: 8px; }
    .stSelectbox > div > div { background: #141414 !important; border-color: #333 !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────
def check_auth():
    if not st.session_state.get("authenticated"):
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            st.markdown("""
            <div style='text-align:center; padding:60px 0 30px;'>
                <div style='font-size:2.5rem; font-weight:800; letter-spacing:0.1em;'>
                    <span style='color:#FF6B00;'>NEETE</span>
                </div>
                <div style='color:#555; font-size:0.85rem; margin-top:4px; letter-spacing:0.15em;'>
                    AI GATEWAY OBSERVABILITY
                </div>
            </div>
            """, unsafe_allow_html=True)
            with st.form("login"):
                pwd = st.text_input("Password", type="password", placeholder="Enter access password")
                if st.form_submit_button("Access Dashboard", use_container_width=True):
                    if pwd == st.secrets["DASHBOARD_PASSWORD"]:
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("Invalid password")
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
        d = r.json() if r.status_code == 200 else []
        return d if isinstance(d, list) else []
    except:
        return []

@st.cache_data(ttl=15)
def fetch_alerts() -> list:
    try:
        r = httpx.get(f"{GATEWAY_URL}/v1/alerts", headers=HEADERS, timeout=10)
        d = r.json() if r.status_code == 200 else []
        return d if isinstance(d, list) else []
    except:
        return []

def auto_refresh(seconds: int = 30):
    st.markdown(
        f"<script>setTimeout(()=>window.location.reload(),{seconds*1000});</script>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:20px 0 10px;'>
        <div style='font-size:1.4rem; font-weight:800; color:#FF6B00; letter-spacing:0.08em;'>NEETE</div>
        <div style='font-size:0.65rem; color:#444; letter-spacing:0.12em;'>AI GATEWAY OBSERVABILITY</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    is_live = fetch_health()
    st.markdown(
        f"<span class='{'status-live' if is_live else 'status-down'}'>{'● LIVE' if is_live else '● DOWN'}</span>",
        unsafe_allow_html=True
    )
    st.caption(datetime.now().strftime("%d %b %Y, %I:%M %p IST"))
    st.divider()

    page = st.radio("", [
        "Overview",
        "Model Analytics",
        "Usage Trends",
        "Alerts",
        "Test LLM",
    ], label_visibility="collapsed")

    st.divider()
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    auto = st.toggle("Auto Refresh (30s)", value=True)
    if auto:
        auto_refresh(30)

    st.markdown("""
    <div style='position:fixed;bottom:16px;left:0;right:0;text-align:center;'>
        <span style='color:#333;font-size:0.65rem;'>Neete IT Division</span>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE 1 — OVERVIEW
# ─────────────────────────────────────────────
if page == "Overview":
    st.markdown("## Gateway Overview")
    st.caption(f"Last updated: {datetime.now().strftime('%I:%M:%S %p IST')}")

    models = fetch_models()
    quota  = fetch_quota()
    keys   = fetch_keys()
    alerts = fetch_alerts()

    # KPI Row
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Models", len(models))
    with c2:
        st.metric("Requests Today", f"{quota.get('requests_today', 0):,}")
    with c3:
        st.metric("Tokens Used", f"{quota.get('tokens_today', 0):,}")
    with c4:
        st.metric("Active Keys", len(keys))
    with c5:
        alert_count = len(alerts)
        st.metric("Active Alerts", alert_count)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Provider Distribution")
        groq_models = [m for m in models if any(
            x in m.get("canonical_name","").lower()
            for x in ["llama","mixtral","gemma","whisper"]
        ) or any(
            p.get("provider") == "groq"
            for p in m.get("providers", [])
        )]
        nim_models = [m for m in models if m not in groq_models]

        fig = go.Figure(data=[go.Pie(
            labels=["Groq", "NVIDIA NIM"],
            values=[len(groq_models), len(nim_models)],
            hole=0.65,
            marker=dict(colors=["#FF6B00", "#CC4400"], line=dict(color="#0A0A0A", width=2)),
            textinfo="label+value",
            textfont=dict(color="white", size=12),
            hovertemplate="%{label}: %{value} models<extra></extra>",
        )])
        fig.update_layout(
            paper_bgcolor="#141414",
            plot_bgcolor="#141414",
            font=dict(color="white"),
            showlegend=False,
            margin=dict(t=10, b=10, l=10, r=10),
            height=260,
            annotations=[dict(
                text=f"<b>{len(models)}</b><br><span style='font-size:10px'>Models</span>",
                x=0.5, y=0.5,
                font=dict(size=18, color="#FF6B00"),
                showarrow=False,
            )]
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### Daily Token Quota")
        DAILY_LIMIT = quota.get("tokens_limit", 500_000) or 500_000
        used        = quota.get("tokens_today", 0)
        remaining   = max(0, DAILY_LIMIT - used)
        pct         = min(100, (used / DAILY_LIMIT) * 100)
        color     = "#00C853" if pct < 60 else "#FF6B00" if pct < 85 else "#FF3D00"

        fig2 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=pct,
            number={"suffix": "%", "font": {"color": color, "size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": "#333", "tickfont": {"color": "#555"}},
                "bar": {"color": color, "thickness": 0.25},
                "bgcolor": "#1A1A1A",
                "bordercolor": "#222",
                "steps": [
                    {"range": [0, 60],  "color": "#0D1A0D"},
                    {"range": [60, 85], "color": "#1A0D00"},
                    {"range": [85, 100],"color": "#1A0000"},
                ],
                "threshold": {"line": {"color": "#FF3D00", "width": 2}, "thickness": 0.75, "value": 85},
            },
        ))
        fig2.update_layout(
            paper_bgcolor="#141414",
            font=dict(color="white"),
            height=240,
            margin=dict(t=20, b=0, l=20, r=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

        ca, cb = st.columns(2)
        ca.metric("Used", f"{used:,}")
        cb.metric("Remaining", f"{remaining:,}")

    st.divider()

    # Model availability table
    st.markdown("#### Model Availability")
    avail_rows = []
    for m in models:
        prov_list = m.get("providers", [])
        provider  = prov_list[0].get("provider", "unknown").upper() if prov_list else "UNKNOWN"
        avail_rows.append({
            "Model": m.get("canonical_name", ""),
            "Display Name": m.get("display_name", ""),
            "Provider": provider,
            "Status": m.get("status", "unknown"),
            "Available Keys": m.get("available_keys", 0),
            "Context Window": m.get("context_window", 0),
        })

    if avail_rows:
        df_avail = pd.DataFrame(avail_rows)
        st.dataframe(
            df_avail,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Context Window": st.column_config.NumberColumn(format="%d tokens"),
            }
        )


# ─────────────────────────────────────────────
# PAGE 2 — MODEL ANALYTICS
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

    model_usage = quota.get("model_usage", {})

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

        # Match usage by provider_model_id (e.g. "llama-3.1-8b-instant")
        # since quota is keyed by provider model ID not canonical name
        provider_model_id = prov_list[0].get("provider_model_id", mid) if prov_list else mid
        usage_entry = (
            model_usage.get(mid) or
            model_usage.get(provider_model_id) or
            {}
        ) if isinstance(model_usage, dict) else {}
        tok_data  = usage_entry.get("tokens", {})
        used      = tok_data.get("used", 0)
        limit     = tok_data.get("limit", 100_000) or 100_000
        remaining = tok_data.get("remaining", limit - used)
        pct       = tok_data.get("pct_used", 0.0)
        req_day   = prov_list[0].get("req_per_day", 0) if prov_list else 0

        req_data  = usage_entry.get("requests", {}) if usage_entry else {}
        req_used  = req_data.get("used", 0)
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
    st.caption("Test any model through the gateway in real-time")

    models = fetch_models()

    # Provider filter for Test LLM
    test_provider = st.radio(
        "Provider", ["Groq (Recommended)", "NVIDIA NIM"],
        horizontal=True,
        help="Groq models are stable. NIM models may return 404 if not available."
    )

    use_groq = "Groq" in test_provider

    # Use verified working models from test report
    WORKING_GROQ = ["llama-3.1-8b", "llama-3.3-70b", "llama-4-scout", "allam-2-7b"]
    WORKING_NIM  = [
        "nemotron-mini-4b-instruct", "mistral-large-3-675b-instruct-2512",
        "gemma-3n-e4b-it", "gemma-3n-e2b-it", "gemma-2-2b-it",
        "llama-4-maverick-17b-128e-instruct", "glm-5.1",
        "mixtral-8x7b-instruct-v0.1", "dracarys-llama-3.1-70b-instruct",
        "llama-3.2-1b-instruct", "llama-3.2-3b-instruct",
        "llama-3.2-90b-vision-instruct", "llama-3.1-nemotron",
        "nemotron-super", "nemotron-3-super-120b-a12b",
        "kimi-k2.6", "llama-3.1-nemotron-nano-vl-8b-v1",
        "llama-3.2-vision", "llama-guard-4-12b",
    ]

    model_ids = WORKING_GROQ if use_groq else WORKING_NIM

    if not model_ids:
        st.error("No models available. Gateway may be unreachable.")
        st.stop()

    st.caption(f"{len(model_ids)} chat-capable models available")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        selected_model = st.selectbox("Model", options=model_ids)
    with col2:
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    with col3:
        max_tokens = st.number_input("Max Tokens", 64, 4096, 512)

    system_prompt = st.text_input(
        "System Prompt",
        placeholder="Optional — e.g. You are a manufacturing assistant for Funcool.",
    )
    user_input = st.text_area("Message", placeholder="Enter your message...", height=100)

    if st.button("Send Request", use_container_width=True):
        if not user_input.strip():
            st.warning("Please enter a message.")
        else:
            with st.spinner(f"Requesting {selected_model}..."):
                messages = []
                if system_prompt.strip():
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": user_input})

                t0 = time.perf_counter()
                try:
                    resp = httpx.post(
                        f"{GATEWAY_URL}/v1/chat",
                        json={"model": selected_model, "messages": messages,
                              "temperature": temperature, "max_tokens": max_tokens},
                        headers=HEADERS,
                        timeout=60,
                    )
                    latency = (time.perf_counter() - t0) * 1000

                    if resp.status_code == 200:
                        data  = resp.json()

                        # Gateway returns custom format: {content, usage, model, provider, latency_ms}
                        # NOT OpenAI choices[] format
                        content = data.get("content") or ""
                        usage   = data.get("usage", {})

                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Latency",           f"{data.get('latency_ms', latency):.0f} ms")
                        m2.metric("Prompt Tokens",     usage.get("prompt_tokens", 0))
                        m3.metric("Completion Tokens", usage.get("completion_tokens", 0))
                        m4.metric("Total Tokens",      usage.get("total_tokens", 0))

                        st.divider()
                        st.markdown("**Response**")
                        st.markdown(f"""
                        <div style='background:#141414; border:1px solid #2A2A2A; border-left:3px solid #FF6B00;
                                    border-radius:8px; padding:20px; color:#DDD;
                                    font-size:0.9rem; line-height:1.7; white-space:pre-wrap;'>{content}</div>
                        """, unsafe_allow_html=True)
                        st.caption(
                            f"Model: {data.get('model', selected_model)}  |  "
                            f"Provider: {data.get('provider','')}  |  "
                            f"Latency: {data.get('latency_ms', latency):.0f}ms"
                        )
                    else:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
