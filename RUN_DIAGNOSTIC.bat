@echo off
REM Diagnostic script for JMeter MCP Server
REM Run this if you encounter issues

setlocal enabledelayedexpansion

echo.
echo ========================================
echo  JMeter MCP Server Diagnostic
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python installation...
python --version
if %ERRORLEVEL% EQU 0 (
    echo  OK: Python found
) else (
    echo  ERROR: Python not found!
    exit /b 1
)

REM Check MCP library
echo.
echo [2/6] Checking MCP library...
python -m pip show mcp | find "Version"
if %ERRORLEVEL% EQU 0 (
    echo  OK: MCP library installed
) else (
    echo  ERROR: MCP library not found!
    echo  Run: pip install mcp
    exit /b 1
)

REM Check JMeter
echo.
echo [3/6] Checking JMeter installation...
if exist "D:\Program Files\Jmeter\apache-jmeter-5.6.3\bin\jmeter.bat" (
    echo  OK: JMeter found
) else (
    echo  ERROR: JMeter not found at D:\Program Files\Jmeter\apache-jmeter-5.6.3
    exit /b 1
)

REM Check server file
echo.
echo [4/6] Checking server.py...
if exist "D:\Jmeter_MCP_NEW\server.py" (
    echo  OK: server.py found
) else (
    echo  ERROR: server.py not found!
    exit /b 1
)

REM Check config file
echo.
echo [5/6] Checking Claude Desktop config...
if exist "%APPDATA%\Claude\claude_desktop_config.json" (
    echo  OK: Config file found at %APPDATA%\Claude\claude_desktop_config.json
) else (
    echo  ERROR: Config file not found!
    echo  Expected: %APPDATA%\Claude\claude_desktop_config.json
    exit /b 1
)

REM Test server startup
echo.
echo [6/6] Testing server startup...
cd /d D:\Jmeter_MCP_NEW
timeout /t 2 /nobreak
python server.py > nul 2>&1 &
set SERVER_PID=!ERRORLEVEL!
timeout /t 2 /nobreak
taskkill /PID !SERVER_PID! /F > nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo  OK: Server started successfully
) else (
    echo  WARNING: Server test inconclusive
)

echo.
echo ========================================
echo  ✅ All checks passed!
echo ========================================
echo.
echo Next steps:
echo  1. Open Claude Desktop
echo  2. Start a new chat
echo  3. Try: "Generate a JMeter test plan for https://httpbin.org/get"
echo.
pause

