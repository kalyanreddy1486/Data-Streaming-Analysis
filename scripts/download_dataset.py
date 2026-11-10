"""
Dataset acquisition and preprocessing script for the UCI Household Electric Power Consumption dataset.
Downloads the official archive, extracts the raw data, formats Date_Time, and prepares sample CSVs.
"""

import os
import zipfile
import urllib.request
import csv
from datetime import datetime

UCI_DATASET_URL = "https://archive.ics.uci.edu/static/public/235/individual+household+electric+power+consumption.zip"
RAW_ZIP_PATH = os.path.join("data", "household_power_consumption.zip")
EXTRACTED_TXT = os.path.join("data", "household_power_consumption.txt")
SAMPLE_CSV_PATH = os.path.join("data", "sample_data.csv")
SAMPLE_DEMO_PATH = os.path.join("data", "household_power_consumption_sample.csv")

def download_and_prepare_dataset(sample_size=15000):
    os.makedirs("data", exist_ok=True)
    
    # 1. Download official UCI zip if not already present
    if not os.path.exists(EXTRACTED_TXT):
        if not os.path.exists(RAW_ZIP_PATH):
            print(f"Downloading official UCI dataset from {UCI_DATASET_URL}...")
            urllib.request.urlretrieve(UCI_DATASET_URL, RAW_ZIP_PATH)
            print("Download completed successfully.")
        
        print("Extracting zip archive...")
        with zipfile.ZipFile(RAW_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall("data")
        print(f"Extracted to {EXTRACTED_TXT}")
    else:
        print(f"Found existing raw dataset: {EXTRACTED_TXT}")

    # 2. Parse and generate standardized CSV files
    print(f"Processing first {sample_size} records into standardized CSV...")
    fieldnames = [
        "Date_Time",
        "Global_active_power",
        "Global_reactive_power",
        "Global_intensity",
        "Sub_metering_1",
        "Sub_metering_2",
        "Sub_metering_3"
    ]

    total_read = 0
    valid_rows = 0
    missing_count = 0

    with open(EXTRACTED_TXT, 'r', encoding='utf-8', errors='ignore') as infile, \
         open(SAMPLE_CSV_PATH, 'w', newline='', encoding='utf-8') as outfile, \
         open(SAMPLE_DEMO_PATH, 'w', newline='', encoding='utf-8') as demofile:
        
        reader = csv.DictReader(infile, delimiter=';')
        writer1 = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer2 = csv.DictWriter(demofile, fieldnames=fieldnames)
        
        writer1.writeheader()
        writer2.writeheader()

        for row in reader:
            total_read += 1
            if valid_rows >= sample_size:
                break
            
            # Check for missing values encoded as '?'
            if row.get('Global_active_power') == '?' or not row.get('Global_active_power'):
                missing_count += 1
                continue
            
            try:
                # Format Date (DD/MM/YYYY) and Time (HH:MM:SS) into YYYY-MM-DD HH:MM:SS
                dt_str = f"{row['Date']} {row['Time']}"
                dt_obj = datetime.strptime(dt_str, "%d/%m/%Y %H:%M:%S")
                formatted_dt = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                
                clean_row = {
                    "Date_Time": formatted_dt,
                    "Global_active_power": float(row["Global_active_power"]),
                    "Global_reactive_power": float(row.get("Global_reactive_power", 0.0) if row.get("Global_reactive_power") != '?' else 0.0),
                    "Global_intensity": float(row.get("Global_intensity", 0.0) if row.get("Global_intensity") != '?' else 0.0),
                    "Sub_metering_1": float(row.get("Sub_metering_1", 0.0) if row.get("Sub_metering_1") != '?' else 0.0),
                    "Sub_metering_2": float(row.get("Sub_metering_2", 0.0) if row.get("Sub_metering_2") != '?' else 0.0),
                    "Sub_metering_3": float(row.get("Sub_metering_3", 0.0) if row.get("Sub_metering_3") != '?' else 0.0),
                }

                writer1.writerow(clean_row)
                writer2.writerow(clean_row)
                valid_rows += 1
            except Exception as e:
                # Log invalid record
                continue

    print(f"Successfully processed {valid_rows} valid records (skipped {missing_count} missing records).")
    print(f"Saved: {SAMPLE_CSV_PATH}")
    print(f"Saved: {SAMPLE_DEMO_PATH}")

if __name__ == "__main__":
    download_and_prepare_dataset(15000)
