@echo off
REM =====================================================================
REM Start Oracle MySQL Server 8.4 Daemon on Port 3306
REM =====================================================================

set MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.4\bin
set MYSQL_DATA=C:\Users\kalya\mysql_data

echo Starting MySQL Server 8.4 on port 3306...
"%MYSQL_BIN%\mysqld.exe" --datadir="%MYSQL_DATA%" --port=3306 --console
pause
