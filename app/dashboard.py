"""
Real-Time Streaming Analytics Dashboard.
Clean, intuitive, and modern dashboard matching MiniProject_Guide.pdf Figure 2.
Zero-flicker WebSocket updating via @st.fragment with live streaming controls,
replay delay pacing, one-click demo reset, and high-visibility architecture status.
"""

import os
import sys
import time
import socket
from datetime import datetime

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from config.settings import get_settings
from config.stream_control import (
    get_stream_state,
    set_stream_active,
    set_replay_delay,
    request_demo_reset,
    is_stream_active,
    get_replay_delay
)
from database.repository import MeterRepository
from database.db_connection import check_db_connection
from app.components import (
    render_power_timeseries_chart,
    render_submetering_chart,
    render_power_distribution_chart
)

# Page configuration
st.set_page_config(
    page_title="StreamPulse | Real-Time Power Analytics & ML Anomaly Radar",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean, Modern, High-Legibility Styling (Matches User's UI Design)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0b0f19;
        color: #f8fafc;
    }
    
    .block-container {
        padding-top: 3.5rem;
        padding-bottom: 2rem;
        max-width: 96%;
    }

    /* Top Command Header */
    .command-header {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 20px 24px;
        margin-top: 6px;
        margin-bottom: 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    
    .command-header, .command-header * {
        color: #ffffff !important;
    }

    /* System Architecture Banner (Moved to prominent top position) */
    .arch-status-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 12px 20px;
        margin-bottom: 16px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }

    .arch-status-title {
        font-size: 14px;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .arch-items-group {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 20px;
        font-size: 13px;
        color: #cbd5e1;
    }

    /* Architecture Badges */
    .badge-code {
        background: rgba(16, 185, 129, 0.12);
        color: #34d399 !important;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 8px;
        border-radius: 4px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 11.5px;
        font-weight: 600;
    }

    /* Crisp High-Contrast KPI Cards */
    .kpi-card {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 15px 12px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
    }
    .kpi-blue::before { background: #38bdf8; }
    .kpi-amber::before { background: #f59e0b; }
    .kpi-purple::before { background: #a855f7; }
    .kpi-green::before { background: #10b981; }
    .kpi-slate::before { background: #94a3b8; }
    .kpi-red::before { background: #ef4444; }

    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        color: #94a3b8;
        letter-spacing: 0.5px;
    }
    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 24px;
        font-weight: 700;
        margin-top: 4px;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 11px;
        color: #64748b;
        margin-top: 4px;
    }

    /* Status Badges */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 500;
    }
    .pill-green {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .pill-red {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .pill-amber {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .pill-blue {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }

    /* Sidebar Custom Styling */
    section[data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid #1e293b;
    }

    .sidebar-section-title {
        font-size: 15px;
        font-weight: 700;
        color: #f8fafc;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 6px;
        margin-bottom: 8px;
    }

    /* Primary Start Button: Red / Coral Accent */
    div[data-testid="stSidebar"] button[kind="primary"] {
        background-color: #ef4444 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.35) !important;
    }

    div[data-testid="stSidebar"] button[kind="primary"]:hover {
        background-color: #dc2626 !important;
    }

    /* Secondary Pause & Reset Buttons */
    div[data-testid="stSidebar"] button[kind="secondary"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
    }

    div[data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #334155 !important;
        border-color: #64748b !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to check Kafka connectivity
def check_kafka_live(bootstrap_servers: str) -> bool:
    try:
        host, port = bootstrap_servers.split(":")
        s = socket.create_connection((host, int(port)), timeout=1.0)
        s.close()
        return True
    except Exception:
        return False

# ==============================================================================
# SIDEBAR CONTROLS (Only Streaming Controls & Live Demo Reset, as requested)
# ==============================================================================
with st.sidebar:
    # 1. Streaming Controls Section
    st.markdown('<div class="sidebar-section-title">🎛️ Streaming Controls</div>', unsafe_allow_html=True)

    stream_state = get_stream_state()
    current_active = bool(stream_state.get("is_streaming", True))
    current_delay = float(stream_state.get("replay_delay", 0.20))

    replay_delay = st.slider(
        "Replay Delay (seconds/reading)",
        min_value=0.05,
        max_value=1.00,
        value=current_delay,
        step=0.05,
        format="%.2f"
    )
    if abs(replay_delay - current_delay) > 0.001:
        set_replay_delay(replay_delay)

    # Start and Pause Stream Buttons Side-by-Side
    col_start, col_pause = st.columns(2)
    with col_start:
        start_clicked = st.button(
            "▶️ Start\nStream",
            key="btn_start_stream",
            use_container_width=True,
            type="primary" if current_active else "secondary"
        )
        if start_clicked:
            set_stream_active(True)
            st.toast("⚡ Telemetry Stream Active (Publishing to Kafka)", icon="▶️")
            st.rerun()

    with col_pause:
        pause_clicked = st.button(
            "⏸️ Pause\nStream",
            key="btn_pause_stream",
            use_container_width=True,
            type="primary" if not current_active else "secondary"
        )
        if pause_clicked:
            set_stream_active(False)
            st.toast("⏸️ Telemetry Stream Paused", icon="⏸️")
            st.rerun()

    st.divider()

    # 2. Live Demo Reset Section
    st.markdown('<div class="sidebar-section-title">🔄 Live Demo Reset</div>', unsafe_allow_html=True)
    reset_clicked = st.button(
        "🗑️ Reset Demo Data to Zero",
        key="btn_reset_demo",
        use_container_width=True,
        type="secondary"
    )
    if reset_clicked:
        success = request_demo_reset()
        if success:
            st.toast("🗑️ Database and stream state reset to zero!", icon="✅")
            st.success("✅ Demo Data Reset to Zero!")
            time.sleep(0.3)
            st.rerun()
        else:
            st.error("❌ Reset failed. Check MySQL connection.")


# ==============================================================================
# MAIN DASHBOARD VIEW
# ==============================================================================

# Top Control & Navigation Bar
st.markdown("""
<div class="command-header">
    <div style="font-size: 26px; line-height: 1.3; margin: 0; padding: 0;">
        <span style="color: #38bdf8 !important; font-weight: 800;">⚡ StreamPulse</span> 
        <span style="color: #ffffff !important; font-weight: 700;">&mdash; Real-Time Power Analytics</span>
    </div>
    <div style="color: #94a3b8 !important; font-size: 13.5px; font-weight: 400; margin-top: 6px;">
        Academic Mini-Project • Apache Kafka 3.7 (KRaft) • 30-Reading Sliding Window • Scikit-Learn Isolation Forest • MySQL 8.4
    </div>
</div>
""", unsafe_allow_html=True)

# Prominently Placed System Architecture Status Card
settings = get_settings()
st.markdown(f"""
<div class="arch-status-card">
    <div class="arch-status-title">
        🖥️ System Architecture Status
    </div>
    <div class="arch-items-group">
        <div>• <b>Database Engine:</b> <span class="badge-code">MYSQL</span></div>
        <div>• <b>Streaming Pipeline:</b> <span class="badge-code">Apache Kafka</span> <span style="color: #34d399; font-family: 'JetBrains Mono', monospace; font-size: 11.5px;">({settings.KAFKA_TOPIC})</span></div>
        <div>• <b>ML Model:</b> <span class="badge-code">Isolation Forest</span> <span style="color: #34d399; font-family: 'JetBrains Mono', monospace; font-size: 11.5px;">(scikit-learn)</span></div>
    </div>
</div>
""", unsafe_allow_html=True)


# Dynamic In-Place Auto-Refreshing Fragment (Continuous zero-flicker 2-second background sync)
@st.fragment(run_every=2)
def live_dashboard_fragment():
    settings = get_settings()
    repo = MeterRepository()
    is_active = is_stream_active()

    # Query MySQL Server for fresh snapshot and latest 120 readings
    db_online = check_db_connection()
    kafka_online = check_kafka_live(settings.KAFKA_BOOTSTRAP_SERVERS)
    metrics = repo.get_latest_metrics() if db_online else None
    
    # 120-reading rolling window
    recent_df = repo.get_recent_readings(limit=120) if db_online else pd.DataFrame()
    anomalies_df = repo.get_recent_anomalies(limit=12) if db_online else pd.DataFrame()

    # Status Indicators Bar
    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        cls = "pill-green" if kafka_online else "pill-red"
        txt = "Kafka: Online (9092)" if kafka_online else "Kafka: Offline"
        st.markdown(f'<span class="status-pill {cls}">● {txt}</span>', unsafe_allow_html=True)

    with stat2:
        cls = "pill-green" if db_online else "pill-red"
        txt = f"MySQL: Online ({settings.MYSQL_DATABASE})" if db_online else "MySQL: Offline"
        st.markdown(f'<span class="status-pill {cls}">● {txt}</span>', unsafe_allow_html=True)

    with stat3:
        if is_active:
            st.markdown('<span class="status-pill pill-green">● Status: Live Streaming</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-pill pill-amber">❚❚ Status: Stream Paused</span>', unsafe_allow_html=True)

    with stat4:
        total_p = metrics.get("total_readings", 0) if metrics else 0
        st.markdown(f'<span class="status-pill pill-blue">📊 Readings Processed: <b>{total_p:,}</b></span>', unsafe_allow_html=True)

    st.write("")

    # 6 Clean, Distinct KPI Cards
    current_p = float(metrics.get("current_power", 0.0)) if metrics else 0.0
    rolling_avg = float(metrics.get("rolling_avg_30", 0.0)) if metrics else 0.0
    peak_p = float(metrics.get("running_peak", 0.0)) if metrics else 0.0
    energy_kwh = float(metrics.get("total_energy_kwh", 0.0)) if metrics else 0.0
    readings_count = int(metrics.get("total_readings", 0)) if metrics else 0
    anomalies_count = int(metrics.get("total_anomalies", 0)) if metrics else 0

    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    with kpi1:
        st.markdown(f"""
        <div class="kpi-card kpi-blue">
            <div class="kpi-label">Current Power</div>
            <div class="kpi-val" style="color: #38bdf8;">{current_p:.3f} <span style="font-size:12px; color:#94a3b8;">kW</span></div>
            <div class="kpi-sub">Instantaneous draw</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="kpi-card kpi-amber">
            <div class="kpi-label">Rolling Avg (30)</div>
            <div class="kpi-val" style="color: #f59e0b;">{rolling_avg:.3f} <span style="font-size:12px; color:#94a3b8;">kW</span></div>
            <div class="kpi-sub">Sliding horizon</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="kpi-card kpi-purple">
            <div class="kpi-label">Peak Power</div>
            <div class="kpi-val" style="color: #c084fc;">{peak_p:.3f} <span style="font-size:12px; color:#94a3b8;">kW</span></div>
            <div class="kpi-sub">Session maximum</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
        <div class="kpi-card kpi-green">
            <div class="kpi-label">Cumulative Energy</div>
            <div class="kpi-val" style="color: #34d399;">{energy_kwh:.4f} <span style="font-size:12px; color:#94a3b8;">kWh</span></div>
            <div class="kpi-sub">Riemann integrated</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi5:
        st.markdown(f"""
        <div class="kpi-card kpi-slate">
            <div class="kpi-label">Readings Streamed</div>
            <div class="kpi-val" style="color: #f1f5f9;">{readings_count:,}</div>
            <div class="kpi-sub">Total event count</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi6:
        st.markdown(f"""
        <div class="kpi-card kpi-red">
            <div class="kpi-label">Anomalies Detected</div>
            <div class="kpi-val" style="color: #f87171;">{anomalies_count}</div>
            <div class="kpi-sub">ML Isolation Forest</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Primary Power Timeseries Chart (Sequential, strictly monotonic, no criss-crossing lines)
    threshold_kw = 5.854  # 1% contamination threshold
    chart_fig = render_power_timeseries_chart(recent_df, threshold_kw=threshold_kw)
    st.plotly_chart(chart_fig, use_container_width=True)

    # Secondary Investigation Tabs
    tab_anom, tab_stream, tab_sub, tab_dist = st.tabs([
        "🚨 Anomaly Log Radar",
        "📋 Live Telemetry Feed",
        "🔌 Circuit Sub-Metering Breakdown",
        "📊 Power Distribution & Histogram"
    ])

    with tab_anom:
        st.markdown("#### 🚨 Isolation Forest Real-Time Anomaly Detections")
        if not anomalies_df.empty:
            anom_display = anomalies_df[[
                "reading_pk", "reading_time", "global_active_power", "rolling_avg_30"
            ]].copy()
            anom_display.rename(columns={
                "reading_pk": "Event ID",
                "reading_time": "Timestamp (UTC)",
                "global_active_power": "Spike Draw (kW)",
                "rolling_avg_30": "Rolling Avg at Event (kW)"
            }, inplace=True)
            anom_display["Status"] = "⚠️ SEVERE LOAD SURGE"
            st.dataframe(anom_display, use_container_width=True, hide_index=True)
        else:
            st.info("No anomalies detected yet. System load is within normal operating limits (< 5.85 kW).")

    with tab_stream:
        st.markdown("#### 📋 Latest 10 Stream Events (MySQL Ingestion)")
        if not recent_df.empty:
            sort_col = "reading_pk" if "reading_pk" in recent_df.columns else "reading_time"
            feed_df = recent_df.sort_values(by=sort_col, ascending=False).head(10)[[
                "reading_pk", "reading_time", "global_active_power", "rolling_avg_30", "is_anomaly"
            ]].copy()

            feed_df.rename(columns={
                "reading_pk": "Event ID",
                "reading_time": "Timestamp",
                "global_active_power": "Active Power (kW)",
                "rolling_avg_30": "Rolling Avg (kW)",
                "is_anomaly": "ML Flag"
            }, inplace=True)

            feed_df["Classification"] = feed_df["ML Flag"].apply(
                lambda x: "🚨 ANOMALY" if x == 1 else "✅ Normal"
            )
            feed_df.drop(columns=["ML Flag"], inplace=True)
            st.dataframe(feed_df, use_container_width=True, hide_index=True)
        else:
            st.info("No records in database yet. Click '▶️ Start Stream' or await initial ingestion...")

    with tab_sub:
        st.markdown("#### 🔌 Circuit Sub-Metering Breakdown Across Sub-Circuits")
        sub_fig = render_submetering_chart(recent_df)
        st.plotly_chart(sub_fig, use_container_width=True)

    with tab_dist:
        st.markdown("#### 📊 Active Power Histogram & Outlier Boundary")
        dist_fig = render_power_distribution_chart(recent_df, threshold_kw=5.854)
        st.plotly_chart(dist_fig, use_container_width=True)

    # Last synced timestamp
    st.caption(f"Database sync: Real-time active (2s WebSocket fragment) • Last check: {datetime.now().strftime('%H:%M:%S')}")

# Mount live fragment
live_dashboard_fragment()

# Clean Footer
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 12px; margin-top: 25px; border-top: 1px solid #1f2937; padding-top: 10px;">
    Real-Time Streaming Analytics Pipeline • Apache Kafka (KRaft) • 30-Reading Sliding Window • Isolation Forest • MySQL 8.4 • Streamlit
</div>
""", unsafe_allow_html=True)
