# Academic Mini-Project Report
## Real-Time Streaming Analytics Using Machine Learning

---

### 1. Abstract
This project presents an end-to-end, production-grade real-time streaming analytics pipeline designed for smart meter electrical telemetry. Built across six decoupled layers—comprising an authentic UCI dataset loader, Apache Kafka 3.7 (KRaft mode) event broker, a stateful Python stream processor maintaining a 30-reading sliding window, an offline-trained Scikit-Learn Isolation Forest machine learning model for live anomaly detection, an Oracle MySQL 8.4 database, and an auto-refreshing Streamlit dashboard—the system ingests and processes telemetry events with sub-second latency. The primary result is a robust, demonstrable streaming architecture that continuously computes rolling statistics, calculates cumulative energy consumption, and flags genuine anomalous power surges without page reloads or data corruption.

---

### 2. Architecture
The architecture strictly follows the six-layer decoupled pattern specified in `MiniProject_Guide.pdf`:

```mermaid
flowchart TD
    subgraph Layer1 [Layer 1: Data Source]
        DS["UCI Household Power Consumption<br/>data/sample_data.csv (15,000 rows)"]
        DL["Data Loader & Validator<br/>producer/data_loader.py"]
        DS --> DL
    end

    subgraph Layer2 [Layer 2: Ingestion & Messaging]
        KP["Kafka Producer<br/>producer/kafka_producer.py"]
        KB["Apache Kafka Broker 3.7 (KRaft)<br/>Topic: smartmeter-events (Port 9092)"]
        DL --> KP
        KP -->|Paced JSON Events (5 Hz)| KB
    end

    subgraph Layer3 [Layer 3: Stream Processing]
        KC["Kafka Consumer Group<br/>processor/stream_processor.py"]
        SW["Sliding Window (deque maxlen=30)<br/>processor/metrics.py"]
        KB --> KC
        KC --> SW
    end

    subgraph Layer4 [Layer 4: Machine Learning Inference]
        IF["Isolation Forest Model<br/>ml/anomaly_model.pkl (contamination=0.01)"]
        SW -->|Global_active_power| IF
        IF -->|Anomaly Flag: 0 or 1| SW
    end

    subgraph Layer5 [Layer 5: Persistence & Database]
        DB[("MySQL 8.4 Database<br/>Tables: meter_readings & meter_metrics")]
        SW -->|Insert Event & Update Snapshot| DB
    end

    subgraph Layer6 [Layer 6: Visualization Dashboard]
        UI["Streamlit Dashboard (Port 8501)<br/>app/dashboard.py & app/components.py"]
        DB -->|Poll Latest 120 Readings (WebSocket Fragment)| UI
    end
```

#### Technology Stack Choices
| Layer | Component | Selected Technology | Technical Rationale |
|---|---|---|---|
| **Layer 1** | Data Source | Python 3.11 + CSV DictReader | Deterministic parsing and rigorous row validation of raw telemetry strings. |
| **Layer 2** | Messaging | Apache Kafka 3.7.0 (KRaft mode) | High-throughput distributed event log; KRaft eliminates ZooKeeper complexity. |
| **Layer 3** | Stream Processing | Python `collections.deque(maxlen=30)` | $O(1)$ constant-time sliding window append and rolling aggregations. |
| **Layer 4** | Machine Learning | Scikit-Learn `IsolationForest` | Unsupervised outlier isolation ideal for multi-modal energy spike detection. |
| **Layer 5** | Database | Oracle MySQL 8.4 LTS | ACID-compliant relational storage with indexed auto-increment primary keys. |
| **Layer 6** | Visualization | Streamlit 1.66 + Plotly Dark | Low-latency in-place WebSocket fragment refreshes without full page reloads. |

---

### 3. Dataset Format & Telemetry Schema
The project uses the authentic **UCI Individual Household Electric Power Consumption** dataset. The data loader validates timestamps and numeric physical constraints, converting raw inputs into standardized JSON events.

#### Example Standardized JSON Event:
```json
{
  "reading_time": "2006-12-16 17:24:00",
  "global_active_power": 2.846,
  "global_reactive_power": 0.250,
  "global_intensity": 12.4,
  "sub_metering_1": 0.0,
  "sub_metering_2": 1.0,
  "sub_metering_3": 17.0
}
```

#### Field Specifications:
- `reading_time`: ISO-8601 formatted timestamp string (`YYYY-MM-DD HH:MM:SS`).
- `global_active_power`: Household global active power in kilowatts (kW) — primary metric.
- `global_reactive_power`: Household global reactive power in kilowatts (kW).
- `global_intensity`: Global current intensity in amperes (A).
- `sub_metering_1`: Energy sub-metering No. 1 (Kitchen: dishwasher, microwave) in Watt-hours.
- `sub_metering_2`: Energy sub-metering No. 2 (Laundry: washing machine, dryer, fridge) in Watt-hours.
- `sub_metering_3`: Energy sub-metering No. 3 (Electric water heater & air conditioner) in Watt-hours.

---

### 4. Implementation: Each Layer with Code Snippets

#### Layer 1: Data Source & Validation (`producer/data_loader.py`)
*Why it exists*: Real smart meters output noisy, missing, or malformed readings. Layer 1 guarantees only sanitized, physically valid readings enter the message queue.

```python
def validate_and_clean_row(self, row: Dict[str, Any]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    raw_active_power = row.get("Global_active_power")
    if raw_active_power is None or str(raw_active_power).strip() in ("?", "", "nan"):
        self.records_skipped += 1
        return None, "Missing mandatory Global_active_power value"

    active_power = float(raw_active_power)
    if active_power < 0:
        self.records_skipped += 1
        return None, f"Negative power reading ({active_power}) is invalid"

    cleaned_event = {
        "reading_time": cleaned_time,
        "global_active_power": round(active_power, 3),
        "global_reactive_power": round(parse_float(row.get("Global_reactive_power")), 3),
        "global_intensity": round(parse_float(row.get("Global_intensity")), 3),
        "sub_metering_1": round(parse_float(row.get("Sub_metering_1")), 3),
        "sub_metering_2": round(parse_float(row.get("Sub_metering_2")), 3),
        "sub_metering_3": round(parse_float(row.get("Sub_metering_3")), 3),
    }
    self.records_valid += 1
    return cleaned_event, None
```

#### Layer 2: Kafka Ingestion & Messaging (`producer/kafka_producer.py`)
*Why it exists*: Decouples the telemetry publisher from downstream analytics, preventing buffer overflow during bursts and enabling distributed consumer scaling.

```python
self.producer = KafkaProducer(
    bootstrap_servers=self.bootstrap_servers,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    acks="all",
    retries=3
)
for event in self.loader.stream_records(loop_continuously=True):
    self.producer.send(self.topic, value=event)
    time.sleep(self.interval_sec)  # 0.2s paced stream (5 Hz)
```

#### Layer 3: Stream Processing & Sliding Window (`processor/metrics.py`)
*Why it exists*: Real-time analytics requires streaming state aggregation. A Python `collections.deque(maxlen=30)` provides an $O(1)$ memory-bounded sliding window.

```python
class StreamingMetricsCalculator:
    def __init__(self, window_size: int = 30):
        self.window = deque(maxlen=window_size)
        self.running_peak = 0.0
        self.total_energy_kwh = 0.0

    def process_reading(self, power_kw: float) -> Tuple[float, float, float]:
        self.window.append(power_kw)
        rolling_avg = sum(self.window) / len(self.window)
        if power_kw > self.running_peak:
            self.running_peak = power_kw
        # Energy integration: 1 minute per reading -> kWh = kW / 60
        self.total_energy_kwh += power_kw / 60.0
        return rolling_avg, self.running_peak, self.total_energy_kwh
```

#### Layer 4: Machine Learning Inference (`ml/predict.py`)
*Why it exists*: Automatically identifies severe abnormal power draws (equipment failure, short circuits) without requiring hardcoded static thresholds.

```python
class AnomalyDetector:
    def __init__(self, model_path: str = "ml/anomaly_model.pkl"):
        self.model = joblib.load(model_path)

    def predict(self, active_power_kw: float) -> Tuple[int, float]:
        features = np.array([[float(active_power_kw)]])
        raw_pred = self.model.predict(features)[0]  # -1 = anomaly, 1 = normal
        score = float(self.model.decision_function(features)[0])
        is_anomaly = 1 if raw_pred == -1 else 0
        return is_anomaly, score
```

#### Layer 5: Relational Persistence (`database/repository.py`)
*Why it exists*: Guarantees durability, enables retrospective analytical queries, and decouples the stream processor from dashboard consumers via indexed relational tables.

```python
cursor.execute("""
    INSERT INTO meter_readings (
        reading_time, global_active_power, global_reactive_power,
        global_intensity, sub_metering_1, sub_metering_2, sub_metering_3,
        rolling_avg_30, is_anomaly
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
""", values)
cursor.execute("""
    UPDATE meter_metrics 
    SET current_power=%s, rolling_avg_30=%s, running_peak=%s,
        total_energy_kwh=%s, total_readings=%s, total_anomalies=%s,
        last_updated=NOW()
    WHERE metric_id=1;
""", metrics_values)
conn.commit()
```

#### Layer 6: Live Visualization Dashboard (`app/dashboard.py`)
*Why it exists*: Translates raw data into actionable visual insights for human operators, rendering a clean 120-reading moving curve with zero screen flicker.

```python
@st.fragment(run_every=2)
def live_dashboard_fragment():
    metrics = repo.get_latest_metrics()
    recent_df = repo.get_recent_readings(limit=120)
    anomalies_df = repo.get_recent_anomalies(limit=12)

    # Render 6 distinct KPI cards
    # Render primary sequential time-series Plotly curve
    chart_fig = render_power_timeseries_chart(recent_df, threshold_kw=5.85)
    st.plotly_chart(chart_fig, use_container_width=True)
```

---

### 5. Machine Learning Model Details
- **Algorithm**: `sklearn.ensemble.IsolationForest`
- **Training Strategy**:
  - Trained offline on 15,000 authentic UCI power consumption records (`data/sample_data.csv`).
  - Tuned with `contamination=0.01` (1% true outlier expectation) and `n_estimators=100`, `random_state=42`.
- **Learned Thresholds & Detection Behavior**:
  - Normal baseline power mean: **1.875 kW**
  - Anomaly detection boundary: Active power **$\ge 5.854\text{ kW}$** up to **$8.698\text{ kW}$**.
  - Power spikes under 5.85 kW (normal evening appliance load) are classified as normal (`0`). Extreme spikes exceeding 5.85 kW trigger an immediate anomaly classification (`1`).
- **Artifacts Saved**:
  - Model weights: `ml/anomaly_model.pkl`
  - Hyperparameters and training summary: `ml/model_metadata.json`

---

### 6. Dashboard & Real-Time Visualization
The dashboard strictly mirrors **Figure 2** of the project specification:

![Live StreamPulse Dashboard](docs/live_dashboard_screenshot.png)

#### How It Stays Live Without Page Reloads:
- Uses native Streamlit `@st.fragment(run_every=2)` decorated function.
- Polls MySQL every 2 seconds over an active persistent WebSocket connection.
- Only the inner DOM fragment re-renders; the browser page, scroll position, and UI tabs never reload or flicker.
- When the Kafka producer is paused, the database numbers freeze in place, proving that live motion is driven by active data ingestion, not client-side timers.

---

### 7. Results & Live Verification Metrics

| Metric | Target Requirement | Measured System Value | Verification Status |
|---|---|---|---|
| **Pipeline Latency** | Sub-second | ~42 ms (Kafka $\to$ MySQL) | **PASSED** |
| **Window Precision** | Exactly 30 readings | 30 readings (`deque maxlen=30`) | **PASSED** |
| **Max Peak Tracking** | Session Maximum | 8.698 kW | **PASSED** |
| **Anomaly Filtering** | Extreme Surges Only | $\ge 5.85\text{ kW}$ (1.0% contamination) | **PASSED** |
| **Automated Tests** | 100% Passing | 13/13 Pytest cases passed | **PASSED** |
| **Criss-Crossing Artifacts** | Zero line overlaps | 0 (Strict monotonic sequential X) | **PASSED** |

---

### 8. Conclusion & Future Extensions

#### Lessons Learned:
1. **Decoupled Architecture**: Running Kafka between data producers and ML stream processors isolates failures and prevents backpressure from slowing down ingestion.
2. **Stateful Window Invariance**: Using an in-memory double-ended queue (`deque`) provides predictable $O(1)$ updates without database round-trips for rolling metrics.
3. **Time-Series Chart Ingestion Ordering**: When streaming cyclical time-series data, time axes must be strictly sorted by primary key sequence to avoid backwards graph trajectories.

#### Future Extensions:
- **Multi-Variate Anomaly Detection**: Expanding the Isolation Forest feature set to evaluate voltage drop and reactive power ratio simultaneously.
- **Kafka Dead-Letter Queue (DLQ)**: Routing malformed JSON payloads to a dedicated error topic for automated audit inspection.
- **Automated Actuator Alerts**: Integrating Twilio/SendGrid Webhooks to dispatch SMS/Email alerts to grid operators whenever severe power anomalies persist across consecutive readings.
