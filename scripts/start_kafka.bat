@echo off
REM =====================================================================
REM Start Apache Kafka in KRaft Mode (No ZooKeeper required)
REM =====================================================================

set JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.21.21-hotspot
set KAFKA_HOME=C:\Users\kalya\kafka\kafka_2.13-3.7.0
set SERVER_CONFIG=C:\Users\kalya\kafka\server.properties

echo Starting Apache Kafka Broker on port 9092 (KRaft mode)...
"%JAVA_HOME%\bin\java.exe" -Xmx1G -Xms512M -cp "%KAFKA_HOME%\libs\*" kafka.Kafka "%SERVER_CONFIG%"
pause
