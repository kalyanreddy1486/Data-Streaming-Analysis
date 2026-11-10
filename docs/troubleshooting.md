# Troubleshooting & FAQ Guide

## 1. Apache Kafka Issues

### Issue: `NoBrokersAvailable` or Connection Refused on `127.0.0.1:9092`
- **Cause**: Kafka broker process is not running.
- **Solution**:
  1. Open a new terminal.
  2. Run the provided script:
     ```powershell
     scripts\start_kafka.bat
     ```
  3. Verify port 9092 is listening:
     ```powershell
     Test-NetConnection -ComputerName 127.0.0.1 -Port 9092
     ```

### Issue: "The input line is too long" in Windows batch scripts
- **Cause**: Windows cmd.exe has an 8192-character command limit when expanding jar wildcards in `kafka-run-class.bat`.
- **Solution**: Use `scripts\start_kafka.bat` or run Java directly with wildcard classpath:
  ```powershell
  & "C:\Program Files\Microsoft\jdk-17.0.21.21-hotspot\bin\java.exe" -Xmx1G -cp "C:\Users\kalya\kafka\kafka_2.13-3.7.0\libs\*" kafka.Kafka "C:\Users\kalya\kafka\server.properties"
  ```

---

## 2. MySQL Database Issues

### Issue: `Can't connect to MySQL server on '127.0.0.1' (10061)`
- **Cause**: MySQL daemon is stopped or not listening on port 3306.
- **Solution**:
  1. Run the MySQL launcher:
     ```powershell
     scripts\start_mysql.bat
     ```
  2. Test connection:
     ```powershell
     py -3.11 -c "from database import check_db_connection; print('MySQL Status:', check_db_connection())"
     ```

### Issue: `Access denied for user 'root'@'localhost'`
- **Cause**: Password configured in `.env` does not match the server credentials.
- **Solution**: Check `.env` file and set `MYSQL_PASSWORD` to your local root password.

---

## 3. Streamlit Dashboard Issues

### Issue: Dashboard displays "No records found in database yet"
- **Cause**: Producer or Stream Processor has not yet sent events to the database.
- **Solution**:
  1. Ensure `stream_processor.py` is running in one terminal.
  2. Ensure `kafka_producer.py` is running in another terminal.
  3. Verify records in MySQL:
     ```powershell
     py -3.11 -c "from database import MeterRepository; print(MeterRepository().get_latest_metrics())"
     ```

### Issue: Dashboard values are not changing
- **Cause**: Producer is paused or has reached the end of the file.
- **Solution**: Check `CONTINUOUS_REPLAY=True` in `.env` to loop the dataset continuously for uninterrupted demonstrations.

---

## 4. Machine Learning Model Issues

### Issue: `Trained model artifact not found at ml/anomaly_model.pkl`
- **Cause**: Offline training script has not been run.
- **Solution**:
  Run the training script once:
  ```powershell
  py -3.11 ml/train_model.py
  ```
