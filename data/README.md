# Smart Meter Dataset Documentation

## Overview
This project uses the official **Individual Household Electric Power Consumption Data Set** hosted by the **UCI Machine Learning Repository**:
- **Source**: [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)
- **Donor**: Georges Hebrail (georges.hebrail '@' edf.fr), Alice Berard
- **Sampling Frequency**: 1 minute intervals

## Schema & Features

| Column Name | Type | Description | Unit |
| :--- | :--- | :--- | :--- |
| `Date_Time` | String / Datetime | Reading timestamp (`YYYY-MM-DD HH:MM:SS`) | Timestamp |
| `Global_active_power` | Float | Household global minute-averaged active power | Kilowatt (kW) |
| `Global_reactive_power`| Float | Household global minute-averaged reactive power | Kilowatt (kW) |
| `Global_intensity` | Float | Household global minute-averaged current intensity | Ampere (A) |
| `Sub_metering_1` | Float | Kitchen energy sub-metering | Watt-hour (active energy) |
| `Sub_metering_2` | Float | Laundry room energy sub-metering | Watt-hour (active energy) |
| `Sub_metering_3` | Float | Electric water heater & air conditioner sub-metering | Watt-hour (active energy) |

## Preprocessing & Validation Rules
1. **Missing Values**: Raw missing values represented by `?` or blank strings are detected. Rows missing critical numerical metrics (`Global_active_power`) are skipped and logged.
2. **Timestamp Formatting**: Original European dates (`DD/MM/YYYY`) and times (`HH:MM:SS`) are standardized into ISO-8601 compatible timestamps (`YYYY-MM-DD HH:MM:SS`).
3. **Replay Capabilities**: The producer reads `sample_data.csv` sequentially with configurable pacing (default: 5 readings/sec) to emulate real-time smart meter stream telemetry.
