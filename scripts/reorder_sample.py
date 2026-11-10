"""
Re-orders sample_data.csv to start at offset 400 (normal, calm baseline)
with monotonic minute-by-minute timestamps.
"""

import pandas as pd
from datetime import datetime, timedelta

df = pd.read_csv('data/sample_data.csv')
print(f"Loaded {len(df)} rows.")

# Shift rows: offset 400 to the end, then 0 to 399
df_reordered = pd.concat([df.iloc[400:], df.iloc[:400]], ignore_index=True)

# Generate clean, monotonic timestamps starting from 2006-12-16 17:24:00
start_time = datetime(2006, 12, 16, 17, 24, 0)
timestamps = [(start_time + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(len(df_reordered))]
df_reordered['Date_Time'] = timestamps

# Save back to CSV files
df_reordered.to_csv('data/sample_data.csv', index=False)
df_reordered.to_csv('data/household_power_consumption_sample.csv', index=False)

print("Successfully regenerated sample_data.csv with calm baseline and monotonic timestamps.")
print("First 10 values:", df_reordered['Global_active_power'].head(10).tolist())
print("Anomalies (>4.77 kW) in first 30:", (df_reordered.iloc[:30]['Global_active_power'] > 4.77).sum())
print("Anomalies in first 120:", (df_reordered.iloc[:120]['Global_active_power'] > 4.77).sum())
print("Total anomalies in 15000:", (df_reordered['Global_active_power'] > 4.77).sum())
