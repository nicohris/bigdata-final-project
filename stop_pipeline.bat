@echo off
REM ============================================
REM Big Data Pipeline Stop Script
REM ============================================

title Big Data Pipeline - Shutdown
color 0C

echo ============================================
echo   STOPPING BIG DATA PIPELINE
echo ============================================
echo.

cd /d "%~dp0"

echo Stopping all containers...
docker-compose down

echo.
echo ============================================
echo   All services stopped successfully!
echo ============================================
echo.
pause
