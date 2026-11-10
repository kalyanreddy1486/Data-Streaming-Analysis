# Real-Time Streaming Analytics Using Machine Learning
### Smart Meter Power Consumption Monitoring & Isolation Forest Anomaly Detection

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-3.7.0%20(KRaft)-red.svg)](https://kafka.apache.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.4%20LTS-orange.svg)](https://www.mysql.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.66-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.8.0-F7931E.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 1. Project Overview
This project is an end-to-end, production-grade academic mini-project demonstrating **Real-Time Streaming Analytics**. It continuously reads smart-meter electricity readings, streams them through **Apache Kafka**, computes real-time sliding window statistical metrics (30-reading rolling average, running session peak, and cumulative energy consumption in kWh), applies an offline-trained **Isolation Forest Machine Learning model** to flag unusual power spikes, stores enriched data in **MySQL**, and renders dynamic visualizations on an **auto-refreshing Streamlit dashboard**.

---

## 2. Six-Layer Architecture

```
Layer 1: Data Source (UCI Household Power Consumption Dataset - CSV/JSONL Replay)
   │
   ▼
Layer 2: Streaming Infrastructure (Apache Kafka 3.7 Topic: smartmeter-events)
   │
   ▼
Layer 3: Stream Processing (Python Sliding Window: deque-30 Rolling Avg, Peak, Energy)
   │
   ├──────► Layer 4: Machine Learning (Scikit-Learn Isolation Forest Anomaly Detection)
   │
   ▼
Layer 5: Database Serving Layer (MySQL 8.4 Tables: meter_readings & meter_metrics)
   │
   ▼
Layer 6: Visualization (Streamlit Live Dashboard Auto-Refreshing every 2 seconds)
```

---

## 3. Technology Stack

| Layer | Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Layer 1** | Data Source | UCI Dataset / Python | Standardized CSV | Smart meter minute readings |
| **Layer 2** | Message Broker | Apache Kafka (KRaft mode) | 3.7.0 | High-throughput distributed event streaming |
| **Layer 3** | Stream Processor | Python | 3.11 | Stateful sliding window metrics computation |
| **Layer 4** | Machine Learning | Scikit-Learn Isolation Forest | 1.8.0 | Unsupervised power spike anomaly detection |
| **Layer 5** | Database | Oracle MySQL Server | 8.4 LTS | Persistent historical log and snapshot serving layer |
| **Layer 6** | Dashboard | Streamlit + Plotly | 1.66 / 7.1 | Live KPI cards and interactive power curve charts |
| **DevOps** | Automation | Pytest, Dotenv | 9.2.0 | Automated testing & configuration |

---

## 4. Project Directory Structure

```
DSA MINI PROJECT/
├── app/
│   ├── __init__.py
│   ├── dashboard.py         # Streamlit real-time dashboard application
│   └── components.py        # Plotly charts, UI metric cards, sub-metering graphs
├── producer/
│   ├── __init__.py
│   ├── kafka_producer.py    # Paced Kafka event publisher (5 readings/sec)
│   └── data_loader.py       # CSV reader, schema validator, missing value cleaner
├── processor/
│   ├── __init__.py
│   ├── stream_processor.py  # Continuous Kafka consumer, ML scorer, MySQL writer
│   ├── kafka_consumer.py    # Resilient Kafka consumer wrapper
│   └── metrics.py           # Stateful sliding window (deque maxlen=30), kWh aggregator
├── ml/
│   ├── __init__.py
│   ├── train_model.py       # Offline Isolation Forest model trainer
│   ├── predict.py           # Microsecond live anomaly scoring engine
│   ├── anomaly_model.pkl    # Serialized model artifact
│   └── model_metadata.json  # Training parameters, statistics, and thresholds
├── database/
│   ├── __init__.py
│   ├── db_connection.py     # MySQL connection factory and health checks
│   ├── db_initializer.py    # Schema initialization and demonstration reset tool
│   ├── schema.sql           # DDL schema for meter_readings & meter_metrics
│   └── repository.py        # Parameterized SQL data access layer
├── data/
│   ├── README.md            # Dataset documentation and provenance
│   ├── sample_data.csv      # 15,000 standardized authentic UCI records
│   └── household_power_consumption_sample.csv
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized configuration dataclass
├── tests/
│   ├── test_data_loader.py  # Unit tests for data loading & validation
│   ├── test_metrics.py      # Unit tests for sliding window & kWh math
│   ├── test_ml.py           # Unit tests for model training & inference
│   ├── test_database.py     # Unit tests for MySQL connectivity & schema
│   └── test_integration.py  # Full end-to-end multi-layer pipeline test
├── docs/
│   ├── architecture.md      # Detailed 6-layer architecture & Mermaid diagrams
│   ├── project_report.md    # Complete 15-section academic report
│   ├── demo_script.md       # 5-10 minute presentation guide & pause-resume experiment
│   └── troubleshooting.md   # FAQs and error resolution steps
├── scripts/
│   ├── download_dataset.py  # Script to download and parse UCI dataset
│   ├── start_kafka.bat      # Windows batch launcher for Kafka KRaft mode
│   └── start_mysql.bat      # Windows batch launcher for MySQL Server
├── .env.example             # Configuration template
├── .env                     # Local configuration
├── .gitignore
├── requirements.txt         # Python dependencies
├── Makefile                 # Make targets
├── run_pipeline.py          # Master single-command pipeline launcher
└── README.md
```

---

## 5. Prerequisites & Quick Setup

### Step 1: Install Python Dependencies
```powershell
py -3.11 -m pip install -r requirements.txt
```

### Step 2: Download the Dataset
The dataset preparation script automatically downloads the official UCI archive, formats European dates into standard timestamps, and creates `data/sample_data.csv`:
```powershell
py -3.11 scripts/download_dataset.py
```

### Step 3: Initialize MySQL Database
Make sure your MySQL server is running (port 3306), then initialize the tables:
```powershell
py -3.11 database/db_initializer.py
```

### Step 4: Train the Machine Learning Model
Train the Isolation Forest model offline:
```powershell
py -3.11 ml/train_model.py
```
*Output: Saves `ml/anomaly_model.pkl` and `ml/model_metadata.json`.*

---

## 6. Running the Complete System

### Option A: Master Launcher (Recommended)
You can start all layers safely in sequence with graceful shutdown handling using:
```powershell
py -3.11 run_pipeline.py
```
Open your browser to: **`http://localhost:8501`**

---

### Option B: Independent Terminal Execution (For Classroom Demo)

#### Terminal 1 — Start Kafka (Port 9092)
```powershell
scripts\start_kafka.bat
```

#### Terminal 2 — Start MySQL (Port 3306)
```powershell
scripts\start_mysql.bat
```

#### Terminal 3 — Start Stream Processor
```powershell
py -3.11 processor/stream_processor.py
```

#### Terminal 4 — Launch Streamlit Dashboard
```powershell
py -3.11 -m streamlit run app/dashboard.py
```
*Access in browser at:* `http://localhost:8501`

#### Terminal 5 — Start Kafka Telemetry Producer
```powershell
py -3.11 producer/kafka_producer.py
```

---

## 7. Running the Automated Tests
Run the complete Pytest suite (13 unit and end-to-end integration tests):
```powershell
py -3.11 -m pytest -v
```

---

## 8. Live Demonstration Procedure
Follow the complete presentation sequence in [`docs/demo_script.md`](docs/demo_script.md):
1. Reset database tables: `py -3.11 -c "from database import reset_database; reset_database()"`
2. Launch the dashboard (`http://localhost:8501`) and start the stream processor.
3. Start the Kafka producer — observe the live power curve, gliding rolling average, and red anomaly points.
4. **Pause the producer**: Observe that the dashboard continues to refresh every 2 seconds, but data values stop changing.
5. **Resume the producer**: Observe immediate resumption of new records and KPI increments.

---

## 9. Academic Project Report
The complete 15-section academic project report is available at:
[`docs/project_report.md`](docs/project_report.md)
