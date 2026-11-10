import subprocess
import os

res = subprocess.run(["powershell", "-Command", "Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' } | Select-Object ProcessId, CommandLine | ConvertTo-Json"], capture_output=True, text=True)
import json
try:
    data = json.loads(res.stdout)
    if isinstance(data, dict):
        data = [data]
    current_pid = os.getpid()
    for p in data:
        pid = p.get("ProcessId")
        cmd = p.get("CommandLine", "") or ""
        if pid == current_pid:
            continue
        if "stream_processor.py" in cmd or "kafka_producer.py" in cmd or "run_pipeline.py" in cmd:
            print(f"Terminating orphaned process PID {pid}: {cmd[:80]}")
            subprocess.run(["taskkill", "/F", "/PID", str(pid)])
except Exception as e:
    print(f"Error checking processes: {e}")
