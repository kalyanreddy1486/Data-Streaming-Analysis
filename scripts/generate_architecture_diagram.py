"""
Generates a publication-quality architecture diagram for:
'REAL-TIME STREAMING ANALYTICS USING MACHINE LEARNING FOR SMART GRID TELEMETRY'
Draws a decoupled 6-tier pipeline with professional boxes, arrows, badges, and labels.
Saves to docs/architecture_diagram.png at 300 DPI.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, ArrowStyle

def create_architecture_diagram(output_path: str = "docs/architecture_diagram.png"):
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")

    # Set background color
    fig.patch.set_facecolor("#ffffff")
    ax.set_facecolor("#ffffff")

    # Pipeline Steps definition
    # 2 rows of 3 columns, or horizontal flow with clean wrapping
    # Let's do a clean 2-row x 3-column snake layout or 6 horizontal blocks across 2 distinct tiers
    # Tier 1 (Top, Left-to-Right): Layer 1 (Source) -> Layer 2 (Kafka Broker) -> Layer 3 (Stream Processing)
    # Tier 2 (Bottom, Right-to-Left or Left-to-Right): Layer 4 (ML Inference) -> Layer 5 (MySQL Database) -> Layer 6 (Streamlit UI)
    
    boxes = [
        # (x, y, w, h, title, subtitle, details, bg_color, border_color)
        {
            "id": "L1",
            "rect": (0.4, 3.0, 2.7, 1.7),
            "tier": "LAYER 1 • SOURCE & PACING",
            "tech": "Python 3.11 DataLoader",
            "desc": "• UCI Power Dataset Archive\n• Timestamp & physical validation\n• Deterministic 5 Hz pacing generator\n• UTF-8 JSON event serialization",
            "bg": "#f8fafc",
            "border": "#0284c7",
            "tag_bg": "#e0f2fe",
            "tag_fg": "#0369a1"
        },
        {
            "id": "L2",
            "rect": (3.65, 3.0, 2.7, 1.7),
            "tier": "LAYER 2 • MESSAGE BROKER",
            "tech": "Apache Kafka 3.7 (KRaft)",
            "desc": "• Event topic: smartmeter-events\n• Native Raft consensus (No ZooKeeper)\n• Partitioned immutable commit log\n• Asynchronous non-blocking transport",
            "bg": "#f8fafc",
            "border": "#ea580c",
            "tag_bg": "#ffedd5",
            "tag_fg": "#c2410c"
        },
        {
            "id": "L3",
            "rect": (6.9, 3.0, 2.7, 1.7),
            "tier": "LAYER 3 • STREAM ENGINE",
            "tech": "collections.deque (N=30)",
            "desc": "• O(1) in-memory sliding window\n• Real-time rolling mean (30 readings)\n• Session peak tracking: Ppeak = max(P)\n• Riemann sum energy integral (kWh)",
            "bg": "#f8fafc",
            "border": "#d97706",
            "tag_bg": "#fef3c7",
            "tag_fg": "#b45309"
        },
        {
            "id": "L4",
            "rect": (6.9, 0.5, 2.7, 1.7),
            "tier": "LAYER 4 • ML ANOMALY RADAR",
            "tech": "Scikit-Learn IsolationForest",
            "desc": "• Unsupervised random partition trees\n• Normalized path length scoring c(n)\n• Contamination = 0.010 (1.0% surges)\n• Sub-millisecond inference (<0.4 ms)",
            "bg": "#f8fafc",
            "border": "#dc2626",
            "tag_bg": "#fee2e2",
            "tag_fg": "#b91c1c"
        },
        {
            "id": "L5",
            "rect": (3.65, 0.5, 2.7, 1.7),
            "tier": "LAYER 5 • RELATIONAL STORE",
            "tech": "Oracle MySQL 8.4 LTS",
            "desc": "• meter_readings: append-only log\n• meter_metrics: singleton snapshot\n• Atomic multi-table commits\n• B-tree indexed range queries",
            "bg": "#f8fafc",
            "border": "#2563eb",
            "tag_bg": "#dbeafe",
            "tag_fg": "#1d4ed8"
        },
        {
            "id": "L6",
            "rect": (0.4, 0.5, 2.7, 1.7),
            "tier": "LAYER 6 • VISUALIZATION",
            "tech": "Streamlit 1.66 + Plotly",
            "desc": "• @st.fragment in-place updates\n• Monotonic X-axis (0 criss-crossing)\n• 6 real-time responsive KPI cards\n• Streaming Controls & Live Reset",
            "bg": "#f8fafc",
            "border": "#16a34a",
            "tag_bg": "#dcfce7",
            "tag_fg": "#15803d"
        }
    ]

    for b in boxes:
        x, y, w, h = b["rect"]
        
        # Main Box Shadow (soft)
        shadow = FancyBboxPatch(
            (x + 0.04, y - 0.04), w, h,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            facecolor="#e2e8f0", edgecolor="none", zorder=1
        )
        ax.add_patch(shadow)

        # Main Box
        box = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            facecolor=b["bg"], edgecolor=b["border"], linewidth=1.5, zorder=2
        )
        ax.add_patch(box)

        # Header Badge Bar
        badge_h = 0.32
        badge = FancyBboxPatch(
            (x + 0.06, y + h - badge_h - 0.06), w - 0.12, badge_h,
            boxstyle="round,pad=0.02,rounding_size=0.06",
            facecolor=b["tag_bg"], edgecolor="none", zorder=3
        )
        ax.add_patch(badge)

        # Header Badge Text
        ax.text(
            x + 0.12, y + h - 0.22, b["tier"],
            fontsize=8.0, fontweight="bold", color=b["tag_fg"],
            va="center", zorder=4
        )

        # Subsystem Name
        ax.text(
            x + 0.12, y + h - 0.52, b["tech"],
            fontsize=9.0, fontweight="bold", color="#0f172a",
            va="center", zorder=4
        )

        # Horizontal subtle line
        ax.plot([x + 0.12, x + w - 0.12], [y + h - 0.65, y + h - 0.65], color="#cbd5e1", linewidth=0.7, zorder=4)

        # Body details
        ax.text(
            x + 0.12, y + 0.50, b["desc"],
            fontsize=7.2, color="#334155", linespacing=1.45,
            va="center", zorder=4
        )

    # Directional Arrows connecting tiers
    arrow_props = dict(
        arrowstyle="-|>,head_length=0.45,head_width=0.25",
        color="#1e293b",
        lw=1.8,
        zorder=5
    )

    # Arrow 1: L1 -> L2 (Source to Kafka)
    ax.annotate("", xy=(3.60, 3.85), xytext=(3.15, 3.85), arrowprops=arrow_props)
    ax.text(3.38, 4.02, "JSON / 5 Hz", fontsize=6.8, fontweight="bold", color="#475569", ha="center")

    # Arrow 2: L2 -> L3 (Kafka to Stream Processor)
    ax.annotate("", xy=(6.85, 3.85), xytext=(6.40, 3.85), arrowprops=arrow_props)
    ax.text(6.62, 4.02, "Consumer Poll", fontsize=6.8, fontweight="bold", color="#475569", ha="center")

    # Arrow 3: L3 -> L4 (Stream Processor down to ML Anomaly Radar)
    ax.annotate("", xy=(8.25, 2.25), xytext=(8.25, 2.95), arrowprops=arrow_props)
    ax.text(8.75, 2.60, "Feature Vector\n[power_kw]", fontsize=6.8, fontweight="bold", color="#475569", ha="center", va="center")

    # Arrow 4: L4 -> L5 (ML to MySQL Database)
    ax.annotate("", xy=(6.40, 1.35), xytext=(6.85, 1.35), arrowprops=arrow_props)
    ax.text(6.62, 1.52, "Enriched Tuple", fontsize=6.8, fontweight="bold", color="#475569", ha="center")

    # Arrow 5: L5 -> L6 (MySQL to Streamlit UI)
    ax.annotate("", xy=(3.15, 1.35), xytext=(3.60, 1.35), arrowprops=arrow_props)
    ax.text(3.38, 1.52, "WebSocket / 2s", fontsize=6.8, fontweight="bold", color="#475569", ha="center")

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none", bbox_inches="tight")
    plt.close()
    print(f"Successfully created high-resolution architecture diagram at: {output_path}")

if __name__ == "__main__":
    create_architecture_diagram()
