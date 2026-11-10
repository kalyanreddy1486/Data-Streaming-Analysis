"""
Master Orchestration and Pipeline Launcher.
Safely initiates all pipeline layers in proper dependency order:
1. Verify MySQL Server & Kafka Broker connectivity
2. Initialize database schema (tables: meter_readings, meter_metrics)
3. Train/Verify offline Isolation Forest ML model
4. Start Kafka Stream Processor
5. Launch Streamlit Live Dashboard
6. Start Kafka Telemetry Producer
7. Handle graceful shutdown on Ctrl+C
"""

import os
import sys
import time
import subprocess
import signal
import socket
import logging
from config.settings import get_settings
from database.db_connection import check_db_connection
from database.db_initializer import initialize_database
from ml.train_model import train_anomaly_model

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def check_port_open(host: str, port: int) -> bool:
    try:
        s = socket.create_connection((host, port), timeout=2)
        s.close()
        return True
    except Exception:
        return False

def main():
    settings = get_settings()
    logger.info("=================================================================")
    logger.info("   REAL-TIME STREAMING ANALYTICS - MASTER PIPELINE LAUNCHER     ")
    logger.info("=================================================================")

    # 1. Check MySQL
    logger.info(f"[Step 1/7] Checking MySQL connection ({settings.MYSQL_HOST}:{settings.MYSQL_PORT})...")
    if not check_db_connection():
        logger.error(
            f"MySQL server is not accessible on {settings.MYSQL_HOST}:{settings.MYSQL_PORT}.\n"
            "Please ensure MySQL is running (e.g. run scripts/start_mysql.bat or start MySQL service)."
        )
        sys.exit(1)
    logger.info("✓ MySQL Server is ONLINE.")

    # 2. Check Kafka
    logger.info(f"[Step 2/7] Checking Kafka broker ({settings.KAFKA_BOOTSTRAP_SERVERS})...")
    k_host, k_port = settings.KAFKA_BOOTSTRAP_SERVERS.split(":")
    if not check_port_open(k_host, int(k_port)):
        logger.error(
            f"Kafka broker is not accessible on {settings.KAFKA_BOOTSTRAP_SERVERS}.\n"
            "Please ensure Kafka is running (e.g. run scripts/start_kafka.bat)."
        )
        sys.exit(1)
    logger.info("✓ Kafka Broker is ONLINE.")

    # 3. Initialize Database Schema
    logger.info("[Step 3/7] Verifying and initializing database schema...")
    if not initialize_database():
        logger.error("Database initialization failed. Exiting.")
        sys.exit(1)
    logger.info("✓ Database schema verified.")

    # 4. Verify / Train ML Model
    logger.info("[Step 4/7] Checking Isolation Forest model artifact...")
    if not os.path.exists(settings.MODEL_PATH):
        logger.info(f"Model artifact not found at {settings.MODEL_PATH}. Training now...")
        train_anomaly_model()
    logger.info("✓ ML model artifact ready.")

    # Subprocess container for graceful teardown
    processes = []

    def cleanup(signum=None, frame=None):
        logger.info("\nGracefully shutting down all streaming components...")
        for name, proc in reversed(processes):
            logger.info(f"Terminating {name} (PID: {proc.pid})...")
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
        logger.info("All pipeline processes terminated cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    python_executable = sys.executable

    import threading

    def stream_logs(proc, name):
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                line_str = line.strip()
                if line_str:
                    logger.info(f"[{name}] {line_str}")
        except Exception:
            pass

    # 5. Start Kafka Stream Processor
    logger.info("[Step 5/7] Starting Stream Processor...")
    processor_proc = subprocess.Popen(
        [python_executable, "-u", "processor/stream_processor.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    threading.Thread(target=stream_logs, args=(processor_proc, "Stream Processor"), daemon=True).start()
    processes.append(("Stream Processor", processor_proc))
    time.sleep(2)  # Allow consumer group coordination
    logger.info("✓ Stream Processor started.")

    # 6. Launch Streamlit Dashboard
    logger.info("[Step 6/7] Launching Streamlit Dashboard (http://localhost:8501)...")
    dashboard_proc = subprocess.Popen(
        [python_executable, "-m", "streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.headless=true"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    processes.append(("Streamlit Dashboard", dashboard_proc))
    time.sleep(2)
    logger.info("✓ Streamlit Dashboard running at http://localhost:8501")

    # 7. Start Kafka Producer
    logger.info("[Step 7/7] Starting Kafka Producer...")
    producer_proc = subprocess.Popen(
        [python_executable, "-u", "producer/kafka_producer.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    threading.Thread(target=stream_logs, args=(producer_proc, "Kafka Producer"), daemon=True).start()
    processes.append(("Kafka Producer", producer_proc))
    logger.info("✓ Kafka Producer is streaming events.")

    logger.info("\n=================================================================")
    logger.info("   PIPELINE RUNNING! Dashboard: http://localhost:8501           ")
    logger.info("   Press Ctrl+C to terminate all services safely.               ")
    logger.info("=================================================================\n")

    # Stream processor monitor loop
    try:
        while True:
            # Check if any process terminated unexpectedly
            for name, proc in processes:
                poll = proc.poll()
                if poll is not None:
                    logger.warning(f"Process {name} exited with code {poll}!")
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()
