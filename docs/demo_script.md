# Live Demonstration Script (5–10 Minutes)
## Real-Time Streaming Analytics Mini-Project

### Objective
To demonstrate that data is moving dynamically through all six architectural layers in real time, that the machine learning model is actively scoring power readings, and that the Streamlit dashboard automatically refreshes against fresh database records.

---

### Step 1: Presentation Setup (1 Minute)
1. **Explain the Architecture**:
   - Briefly present the six layers: Data Source $\rightarrow$ Apache Kafka $\rightarrow$ Stream Processor $\rightarrow$ Isolation Forest $\rightarrow$ MySQL $\rightarrow$ Streamlit Dashboard.
   - Point out that MySQL acts as the serving layer between the processor and dashboard, preventing browser hangs.

2. **Reset Database Tables (Demonstration Clean Slate)**:
   Open a PowerShell terminal and run:
   ```powershell
   py -3.11 -c "from database import reset_database; reset_database()"
   ```
   *Explanation*: "We reset the database so evaluators can observe the total count, peak, and energy starting cleanly from zero."

---

### Step 2: Starting Infrastructure & Dashboard (2 Minutes)
1. **Verify Services**:
   - Kafka Broker is running on port 9092.
   - MySQL Server is running on port 3306.

2. **Start the Streamlit Dashboard**:
   Open Terminal 1:
   ```powershell
   py -3.11 -m streamlit run app/dashboard.py
   ```
   Open your browser to: `http://localhost:8501`
   - Show the evaluators that the dashboard loads immediately.
   - Point out the status indicators: **Kafka Online**, **MySQL Online**, and all 6 KPI cards showing 0.0 values.

3. **Start the Stream Processor**:
   Open Terminal 2:
   ```powershell
   py -3.11 processor/stream_processor.py
   ```
   *Explanation*: "The processor loads the offline-trained Isolation Forest model into memory once and connects to the `smartmeter-events` Kafka topic."

---

### Step 3: Starting Ingestion & Observing Real-Time Analytics (3 Minutes)
1. **Start the Kafka Producer**:
   Open Terminal 3:
   ```powershell
   py -3.11 producer/kafka_producer.py
   ```
2. **Watch the Dashboard Come Alive**:
   - Bring browser window to the forefront.
   - Notice: **Without touching the keyboard or mouse**, the dashboard automatically refreshes every 2 seconds.
   - The **Current Power** metric begins updating dynamically (e.g. 4.216 kW, 5.360 kW).
   - The **30-Min Rolling Average** begins computing and lagging smoothly behind the raw power spikes.
   - The **Peak Power** updates whenever a new session maximum is observed.
   - The **Total Energy (kWh)** increments continuously ($\sum \frac{\text{kW}}{60}$).
   - In the graph, watch the blue power line extend, the amber rolling average curve glide, and **vivid red markers** appear on spikes detected as anomalies by the Isolation Forest model!

---

### Step 4: The Crucial Demonstration Experiment (Pause & Resume) (2 Minutes)
*This test proves to evaluators that the dashboard is genuinely connected to live streaming ingestion rather than running a canned script.*

1. **Pause the Producer**:
   Go to Terminal 3 (Producer) and press `Ctrl+C` (or minimize it).
2. **Observe the Dashboard**:
   - Point out that the server clock in the top-right continues ticking.
   - The browser continues its 2-second refresh cycle.
   - **However, the data numbers stop advancing**, and the **Data Pipeline** status shifts to **Idle / Paused**.
   - *Explanation to Evaluators*: "This conclusively proves the core streaming principle from Section 8 of the guide: streaming ingestion and dashboard auto-refresh are decoupled. A refreshing dashboard without incoming data remains frozen at the last state."
3. **Resume the Producer**:
   In Terminal 3, restart the producer:
   ```powershell
   py -3.11 producer/kafka_producer.py
   ```
4. **Observe the Immediate Recovery**:
   - New readings immediately start flowing into Kafka and MySQL.
   - The dashboard instantly resumes drawing new points and updating KPIs!

---

### Step 5: Verification via Direct Database Query (1 Minute)
Open a fourth terminal to prove that Streamlit is reading from MySQL, not internal memory:
```powershell
py -3.11 -c "from database import MeterRepository; repo = MeterRepository(); print('Direct DB Snapshot:', repo.get_latest_metrics())"
```
The output matches the exact numbers displayed on the Streamlit dashboard KPI cards.

---

### Step 6: Summary & Conclusion (1 Minute)
Conclude the presentation:
- All 6 layers are working end-to-end.
- Model train/serve split achieves microsecond inference.
- The pipeline handles service interruptions cleanly.
