@echo off
REM =====================================================================
REM One-Click Launcher for Real-Time Streaming Analytics Project
REM =====================================================================

cd /d "%~dp0"
call .venv\Scripts\activate.bat
python run_pipeline.py
pause

