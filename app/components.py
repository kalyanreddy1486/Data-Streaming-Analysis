"""
Executive UI Visualizers and High-Fidelity Chart Generators.
Crafts clean, understandable, and crisp Plotly visualizations strictly matching
MiniProject_Guide.pdf Figure 2: Power Draw - Live (last 120 readings).
"""

import plotly.graph_objects as go
import pandas as pd
from typing import Optional

def render_power_timeseries_chart(df: pd.DataFrame, threshold_kw: float = 5.85) -> go.Figure:
    """
    Renders an executive-grade, crystal-clear real-time power consumption curve:
    - Strictly monotonic numerical X-axis (0..N) ensuring zero criss-crossing lines
    - Clean, human-readable time labels on X-axis ticks (e.g., 17:24:00)
    - Active Power (kW) in Vibrant Cyan with subtle gradient area fill
    - 30-Reading Rolling Average in Warm Amber
    - Anomaly Threshold reference line at ~5.85 kW
    - High-visibility Ruby-Red circular markers on genuine ML anomalies
    """
    fig = go.Figure()

    if df.empty or "reading_time" not in df.columns:
        fig.add_annotation(
            text="📡 Waiting for streaming telemetry from Kafka...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color="#94a3b8")
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            height=420
        )
        return fig

    # Ensure chronological order by reading_pk
    clean_df = df.copy()
    if "reading_pk" in clean_df.columns:
        clean_df = clean_df.sort_values(by="reading_pk", ascending=True).reset_index(drop=True)

    n_points = len(clean_df)
    x_indices = list(range(n_points))

    def format_time_label(val):
        s = str(val)
        if len(s) >= 19:
            return s[11:19]  # "HH:MM:SS"
        return s

    # Generate evenly spaced clean time ticks (6 to 8 ticks max for high legibility)
    step = max(1, n_points // 7)
    sample_indices = list(range(0, n_points, step))
    if sample_indices[-1] != n_points - 1:
        sample_indices.append(n_points - 1)

    tick_vals = [x_indices[i] for i in sample_indices]
    tick_texts = [format_time_label(clean_df["reading_time"].iloc[i]) for i in sample_indices]

    # Pre-build customdata for rich, instant hover inspection
    custom_data = []
    for idx, row in clean_df.iterrows():
        custom_data.append([
            str(row.get("reading_time", "")),
            int(row.get("reading_pk", idx + 1)),
            float(row.get("rolling_avg_30", 0.0))
        ])

    # 1. Actual Power Trace (Clean Vibrant Cyan Line with subtle soft fill)
    fig.add_trace(go.Scatter(
        x=x_indices,
        y=clean_df["global_active_power"],
        mode="lines",
        name="Active Power (kW)",
        line=dict(color="#38bdf8", width=2.4),
        fill="tozeroy",
        fillcolor="rgba(56, 189, 248, 0.05)",
        customdata=custom_data,
        hovertemplate="<b>Timestamp:</b> %{customdata[0]}<br>"
                      "<b>Reading #:</b> %{customdata[1]}<br>"
                      "<b>Active Power:</b> %{y:.3f} kW<br>"
                      "<b>Rolling Avg:</b> %{customdata[2]:.3f} kW<extra></extra>"
    ))

    # 2. 30-Reading Rolling Average Trace (Smooth Warm Amber Line)
    if "rolling_avg_30" in clean_df.columns:
        fig.add_trace(go.Scatter(
            x=x_indices,
            y=clean_df["rolling_avg_30"],
            mode="lines",
            name="30-Reading Rolling Avg (kW)",
            line=dict(color="#f59e0b", width=2.6),
            customdata=custom_data,
            hovertemplate="<b>Timestamp:</b> %{customdata[0]}<br>"
                          "<b>Rolling Avg (30):</b> %{y:.3f} kW<extra></extra>"
        ))

    # 3. Anomaly Threshold Reference Line (Red Dashed Line)
    fig.add_hline(
        y=threshold_kw,
        line_dash="dot",
        line_color="#ef4444",
        line_width=1.8,
        annotation_text=f"Anomaly Threshold (~{threshold_kw:.2f} kW)",
        annotation_position="top right",
        annotation_font=dict(size=12, color="#ef4444", family="Inter, sans-serif")
    )

    # 4. Anomaly Markers (High-visibility Ruby-Red Circular Markers on spikes)
    if "is_anomaly" in clean_df.columns:
        anomalies_mask = clean_df["is_anomaly"] == 1
        anom_x = [x_indices[i] for i, is_anom in enumerate(anomalies_mask) if is_anom]
        anom_y = clean_df.loc[anomalies_mask, "global_active_power"].tolist()
        anom_custom = [custom_data[i] for i, is_anom in enumerate(anomalies_mask) if is_anom]

        if len(anom_x) > 0:
            fig.add_trace(go.Scatter(
                x=anom_x,
                y=anom_y,
                mode="markers",
                name="🚨 Anomaly Detected (ML)",
                marker=dict(
                    color="#ef4444",
                    size=12,
                    symbol="circle",
                    line=dict(color="#ffffff", width=1.8)
                ),
                customdata=anom_custom,
                hovertemplate="<b>⚠️ ML ANOMALY SPIKE DETECTED!</b><br>"
                              "<b>Timestamp:</b> %{customdata[0]}<br>"
                              "<b>Reading #:</b> %{customdata[1]}<br>"
                              "<b>Spike Draw:</b> %{y:.3f} kW<extra></extra>"
            ))

    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text="<b>⚡ Telemetry Stream: Active Power Draw vs. Rolling Average (Last 120 Readings)</b>",
            font=dict(size=16, color="#f8fafc", family="Inter, sans-serif")
        ),
        xaxis=dict(
            title="<b>Timeline (HH:MM:SS) — Sequential Telemetry Stream</b>",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_texts,
            showgrid=True,
            gridcolor="#1f2937",
            tickfont=dict(color="#9ca3af", size=11),
            zeroline=False
        ),
        yaxis=dict(
            title="<b>Power Consumption (kW)</b>",
            showgrid=True,
            gridcolor="#1f2937",
            tickfont=dict(color="#9ca3af", size=11),
            rangemode="tozero",
            zeroline=False
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color="#e2e8f0", size=12)
        ),
        margin=dict(l=50, r=30, t=55, b=50),
        hovermode="x unified",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        height=420,
        uirevision="live_power_chart"
    )

    return fig

def render_submetering_chart(df: pd.DataFrame) -> go.Figure:
    """
    Renders sub-metering breakdown across Kitchen, Laundry, and Climate/Heater.
    """
    fig = go.Figure()
    if df.empty or "sub_metering_1" not in df.columns:
        return fig

    clean_df = df.copy()
    if "reading_pk" in clean_df.columns:
        clean_df = clean_df.sort_values(by="reading_pk", ascending=True).reset_index(drop=True)

    n_points = len(clean_df)
    x_indices = list(range(n_points))

    def format_time_label(val):
        s = str(val)
        if len(s) >= 19:
            return s[11:19]
        return s

    step = max(1, n_points // 7)
    sample_indices = list(range(0, n_points, step))
    if sample_indices[-1] != n_points - 1:
        sample_indices.append(n_points - 1)

    tick_vals = [x_indices[i] for i in sample_indices]
    tick_texts = [format_time_label(clean_df["reading_time"].iloc[i]) for i in sample_indices]

    fig.add_trace(go.Scatter(
        x=x_indices, y=clean_df["sub_metering_1"],
        mode="lines", name="Kitchen (Sub 1)",
        line=dict(color="#10b981", width=2.0),
        hovertemplate="Kitchen: %{y:.1f} Wh<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=x_indices, y=clean_df["sub_metering_2"],
        mode="lines", name="Laundry (Sub 2)",
        line=dict(color="#6366f1", width=2.0),
        hovertemplate="Laundry: %{y:.1f} Wh<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=x_indices, y=clean_df["sub_metering_3"],
        mode="lines", name="Climate/Heater (Sub 3)",
        line=dict(color="#ec4899", width=2.2),
        hovertemplate="Climate/Heater: %{y:.1f} Wh<extra></extra>"
    ))

    fig.update_layout(
        template="plotly_dark",
        title=dict(
            text="<b>🔌 Circuit Sub-Metering Load Decomposition (Watt-hours)</b>",
            font=dict(size=15, color="#f8fafc", family="Inter, sans-serif")
        ),
        xaxis=dict(
            title="Timeline (HH:MM:SS)",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_texts,
            showgrid=True,
            gridcolor="#1f2937",
            tickfont=dict(color="#9ca3af", size=10)
        ),
        yaxis=dict(title="Watt-hours (Wh)", showgrid=True, gridcolor="#1f2937", tickfont=dict(color="#9ca3af")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color="#e2e8f0")),
        margin=dict(l=45, r=25, t=45, b=40),
        hovermode="x unified",
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        height=320,
        uirevision="submeter_chart"
    )
    return fig

def render_power_distribution_chart(df: pd.DataFrame, threshold_kw: float = 4.77) -> go.Figure:
    """
    Renders histogram distribution of active power consumption.
    """
    fig = go.Figure()
    if df.empty or "global_active_power" not in df.columns:
        return fig

    fig.add_trace(go.Histogram(
        x=df["global_active_power"],
        nbinsx=35,
        name="Power Frequency",
        marker=dict(color="#38bdf8", line=dict(color="#0f172a", width=1)),
        opacity=0.85
    ))

    fig.add_vline(
        x=threshold_kw,
        line_dash="dot",
        line_color="#ef4444",
        line_width=2,
        annotation_text=f"Anomaly Threshold ({threshold_kw:.2f} kW)",
        annotation_position="top right",
        annotation_font=dict(size=11, color="#ef4444")
    )

    fig.update_layout(
        template="plotly_dark",
        title=dict(text="<b>📊 Active Power Consumption Distribution (kW)</b>", font=dict(size=15, color="#f8fafc")),
        xaxis=dict(title="Active Power (kW)", showgrid=True, gridcolor="#1f2937"),
        yaxis=dict(title="Reading Frequency", showgrid=True, gridcolor="#1f2937"),
        margin=dict(l=45, r=25, t=45, b=40),
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        height=320,
        showlegend=False,
        uirevision="power_dist_chart"
    )
    return fig
