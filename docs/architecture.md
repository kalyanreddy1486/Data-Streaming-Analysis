# Six-Layer System Architecture Documentation

## Project Title
**Real-Time Streaming Analytics Using Machine Learning: Smart Meter Power Consumption Monitoring & Anomaly Detection**

---

## 1. High-Level Architecture Overview
The system is constructed upon a decoupled, resilient, six-layer real-time data streaming pipeline. Raw telemetry flows sequentially from historical or simulated IoT feeds through high-throughput messaging, stateful stream processing, machine learning inference, database persistence, and a live auto-refreshing user presentation dashboard.

```mermaid
graph TD
    subgraph Layer 1: Data Source
        DS[UCI Household Electric Power Dataset<br/>data/sample_data.csv] -->|Raw Rows| DL[Data Loader & Validator<br/>producer/data_loader.py]
    end

    subgraph Layer 2: Streaming Infrastructure
        DL -->|Validated JSON Events| KP[Kafka Producer<br/>producer/kafka_producer.py]
        KP -->|Paced Stream (5 events/sec)| KT[(Kafka Topic:<br/>smartmeter-events)]
    end

    subgraph Layer 3: Stream Processing
        KT -->|Continuous Polling| KC[Kafka Consumer<br/>processor/kafka_consumer.py]
        KC --> SP[Python Stream Processor<br/>processor/stream_processor.py]
        SP --> SW[Sliding Window Engine<br/>collections.deque(maxlen=30)<br/>- 30-reading Rolling Average<br/>- Running Session Peak<br/>- Cumulative kWh Energy]
    end

    subgraph Layer 4: Machine Learning
        TR[Offline Model Trainer<br/>ml/train_model.py] -.->|Fits Once on Historical Data| MA[(Model Artifact:<br/>ml/anomaly_model.pkl)]
        MA -.->|Loaded Once at Startup| IF[Isolation Forest Detector<br/>ml/predict.py]
        SP -->|Score Active Power| IF
        IF -->|Anomaly Flag: 0/1| SP
    end

    subgraph Layer 5: Database Serving Layer
        SP -->|Persist Enriched Event| DB1[(MySQL Table:<br/>meter_readings)]
        SP -->|Update Singleton Snapshot| DB2[(MySQL Table:<br/>meter_metrics)]
    end

    subgraph Layer 6: Presentation Dashboard
        DB1 -.->|SQL Query (Last 120 Rows)| ST[Streamlit Real-Time Dashboard<br/>app/dashboard.py]
        DB2 -.->|SQL Query (Latest Snapshot)| ST
        ST -->|Auto-refresh every 2s| UI[Live Interactive Dashboard<br/>- 6 KPI Metric Cards<br/>- Real-Time Time Series Chart<br/>- Vivid Red Anomaly Markers<br/>- Energy Sub-metering & Table]
    end

    classDef primary fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef storage fill:#0f172a,stroke:#f59e0b,stroke-width:2px,color:#f8fafc;
    classDef ml fill:#312e81,stroke:#a855f7,stroke-width:2px,color:#f8fafc;
    class DS,DL,KP,KC,SP,SW,ST,UI primary;
    class KT,DB1,DB2 storage;
    class TR,MA,IF ml;
```

---

## 2. Detailed Layer Specifications

### Layer 1 — Data Source (`producer/data_loader.py`)
- **Dataset**: UCI Machine Learning Repository *Individual Household Electric Power Consumption*.
- **Validation**:
  - Missing value detection (`?`, blanks, `NaN`).
  - Strict timestamp parsing to standard ISO datetime (`YYYY-MM-DD HH:MM:SS`).
  - Physical boundary checks (`Global_active_power >= 0.0`).
- **Format**: Normalized JSON telemetry dictionaries containing active power, reactive power, current intensity, and three sub-metering circuits.

### Layer 2 — Streaming Infrastructure (Apache Kafka)
- **Broker**: Apache Kafka 3.7.0 running in modern **KRaft mode** (eliminating legacy ZooKeeper dependencies).
- **Topic**: `smartmeter-events` (1 partition, replication factor 1).
- **Producer**: Paced message emission (configurable, default 0.2s = 5 events/sec) to emulate real-time smart meter network activity.
- **Serialization**: UTF-8 encoded JSON.

### Layer 3 — Stream Processing (`processor/stream_processor.py`, `processor/metrics.py`)
- **Stateful Engine**: Memory-resident sliding window using `collections.deque(maxlen=30)`.
- **Sliding Window Aggregation**:
  $$\text{Rolling Average} = \frac{\sum_{i=1}^{W} P_i}{W} \quad (W \le 30)$$
- **Running Session Peak**:
  $$\text{Peak} = \max(\text{Peak}_{\text{prior}}, P_{\text{current}})$$
- **Cumulative Energy Consumption**:
  Per-minute average power draw (kW) converted to energy in kilowatt-hours (kWh):
  $$\text{Energy (kWh)} = \frac{\sum P_{\text{reading}}}{60}$$

### Layer 4 — Machine Learning (`ml/train_model.py`, `ml/predict.py`)
- **Algorithm**: Scikit-Learn `IsolationForest`.
- **Architectural Pattern**: **Train / Serve Split**:
  1. *Offline Training (once)*: Trained on historical data with `contamination=0.01` and `random_state=42`. Serialized via `joblib` into `ml/anomaly_model.pkl`.
  2. *Live Serving (microsecond latency)*: Loaded once into memory upon stream processor startup. Evaluates each incoming event without retraining.
- **Anomaly Interpretation**: Prediction $+1$ (inlier/normal) $\rightarrow 0$; Prediction $-1$ (outlier/anomaly) $\rightarrow 1$.

### Layer 5 — Database Serving Layer (MySQL 8.4)
- **Database**: `smartmeter`
- **Tables**:
  - `meter_readings`: Historical event log containing time, raw telemetry, rolling average, and anomaly flag.
  - `meter_metrics`: Singleton snapshot row (`metric_id=1`) updated in constant $O(1)$ time containing instantaneous power, rolling average, running peak, total kWh, and anomaly counter.
- **Decoupling Guarantee**: The processor writes to MySQL; the dashboard reads from MySQL. The presentation view never touches the message broker directly.

### Layer 6 — Visualization Layer (Streamlit & Plotly)
- **Auto-Refresh**: Native 2-second periodic reload via `<meta http-equiv='refresh' content='2'>`.
- **Live Visuals**:
  - 6 KPI metric tiles: Current Power, 30-min Rolling Avg, Peak Draw, Total Energy, Total Readings, Anomalies Detected.
  - Interactive Plotly time-series chart showing dynamic power curves and red anomaly scatter points.
  - Sub-metering load distribution graph and recent telemetry records table.
  - Real-time pipeline health badges (Kafka, MySQL, Freshness).
