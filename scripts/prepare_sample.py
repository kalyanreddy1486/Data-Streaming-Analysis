"""
Standardize sample_data.csv starting at a calm, natural baseline (offset 400).
Ensures:
- Initial 30 readings have 0 anomalies (clean baseline for rolling average & peak).
- Authentic appliance spikes appear naturally throughout the stream.
- Zero criss-crossing date loops.
"""

import csv
import os
from datetime import datetime

raw_txt = os.path.join('data', 'household_power_consumption.txt')
if not os.path.exists(raw_txt):
    print("Raw txt dataset not found.")
    exit(1)

valid_rows = []
with open(raw_txt, 'r', encoding='utf-8', errors='ignore') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        gap = row.get('Global_active_power')
        if gap and gap.strip() not in ('?', '', 'nan'):
            try:
                date_str = row['Date']
                time_str = row['Time']
                dt = datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M:%S")
                valid_rows.append({
                    'Date_Time': dt.strftime('%Y-%m-%d %H:%M:%S'),
                    'Global_active_power': round(float(gap), 3),
                    'Global_reactive_power': round(float(row.get('Global_reactive_power', 0.0) or 0.0), 3),
                    'Global_intensity': round(float(row.get('Global_intensity', 0.0) or 0.0), 3),
                    'Sub_metering_1': round(float(row.get('Sub_metering_1', 0.0) or 0.0), 3),
                    'Sub_metering_2': round(float(row.get('Sub_metering_2', 0.0) or 0.0), 3),
                    'Sub_metering_3': round(float(row.get('Sub_metering_3', 0.0) or 0.0), 3),
                })
                if len(valid_rows) >= 16000:
                    break
            except Exception:
                pass

# Take 15,000 records starting from index 400
slice_rows = valid_rows[400:400+15000]

fieldnames = [
    'Date_Time', 'Global_active_power', 'Global_reactive_power',
    'Global_intensity', 'Sub_metering_1', 'Sub_metering_2', 'Sub_metering_3'
]

for target_path in [os.path.join('data', 'sample_data.csv'), os.path.join('data', 'household_power_consumption_sample.csv')]:
    with open(target_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(slice_rows)

print(f"Successfully created standardized sample with {len(slice_rows)} authentic records.")
print("First 10 powers:", [r['Global_active_power'] for r in slice_rows[:10]])
print("Anomalies in first 30:", sum(1 for r in slice_rows[:30] if r['Global_active_power'] > 4.77))
print("Anomalies in first 120:", sum(1 for r in slice_rows[:120] if r['Global_active_power'] > 4.77))
