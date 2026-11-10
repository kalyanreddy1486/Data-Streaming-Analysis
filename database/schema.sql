-- =====================================================================
-- DATABASE INITIALIZATION SCHEMA FOR SMART METER STREAMING ANALYTICS
-- =====================================================================

CREATE DATABASE IF NOT EXISTS smartmeter;
USE smartmeter;

-- ---------------------------------------------------------------------
-- Table 1: Historical processed readings stream
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meter_readings (
    reading_pk BIGINT AUTO_INCREMENT PRIMARY KEY,
    reading_time DATETIME NOT NULL,
    global_active_power DECIMAL(10,3) NOT NULL,
    global_reactive_power DECIMAL(10,3) DEFAULT 0.000,
    global_intensity DECIMAL(10,3) DEFAULT 0.000,
    sub_metering_1 DECIMAL(10,3) DEFAULT 0.000,
    sub_metering_2 DECIMAL(10,3) DEFAULT 0.000,
    sub_metering_3 DECIMAL(10,3) DEFAULT 0.000,
    rolling_avg_30 DECIMAL(10,3) NOT NULL,
    is_anomaly TINYINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_reading_time (reading_time),
    INDEX idx_is_anomaly (is_anomaly)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Table 2: Latest real-time system metrics snapshot
-- Uses a single-row design (id=1) for constant O(1) KPI retrieval
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS meter_metrics (
    metric_id INT PRIMARY KEY,
    current_power DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    rolling_avg_30 DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    running_peak DECIMAL(10,3) NOT NULL DEFAULT 0.000,
    total_energy_kwh DECIMAL(12,4) NOT NULL DEFAULT 0.0000,
    total_readings BIGINT NOT NULL DEFAULT 0,
    total_anomalies BIGINT NOT NULL DEFAULT 0,
    last_updated DATETIME NOT NULL
) ENGINE=InnoDB;

-- Initialize the snapshot row if not present
INSERT INTO meter_metrics (
    metric_id, current_power, rolling_avg_30, running_peak, 
    total_energy_kwh, total_readings, total_anomalies, last_updated
) VALUES (
    1, 0.000, 0.000, 0.000, 0.0000, 0, 0, NOW()
) ON DUPLICATE KEY UPDATE metric_id=1;
