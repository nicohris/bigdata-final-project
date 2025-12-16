@echo off
REM ============================================
REM Big Data Pipeline Startup Script
REM Social Media Monitoring System
REM ============================================

title Big Data Pipeline Launcher
color 0A

echo ============================================
echo   BIG DATA PIPELINE - STARTUP SCRIPT
echo   Social Media Monitoring System
echo ============================================
echo.

REM Navigate to script directory
cd /d "%~dp0"

echo [1/6] Starting Docker containers...
echo.
docker-compose up -d

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start Docker containers!
    echo Make sure Docker Desktop is running.
    pause
    exit /b 1
)

echo.
echo [2/6] Waiting for services to start (45 seconds)...
echo        Please wait, ElasticSearch needs time to initialize...
timeout /t 45 /nobreak >nul

echo.
echo [3/6] Checking ElasticSearch connection...
:check_es
curl -s http://localhost:9200 >nul 2>&1
if %errorlevel% neq 0 (
    echo        ElasticSearch not ready, waiting 5 more seconds...
    timeout /t 5 /nobreak >nul
    goto check_es
)
echo        ElasticSearch is ready!

echo.
echo [4/6] Creating Kafka topics...
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic tweets_raw --partitions 6 --replication-factor 1 2>nul
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic tweets_processed --partitions 6 --replication-factor 1 2>nul
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --create --if-not-exists --topic tweets_alerts --partitions 2 --replication-factor 1 2>nul
echo        Kafka topics created successfully!

echo.
echo [5/6] Checking ElasticSearch index...
python src/utils/load_sample_data.py

echo.
echo [6/6] Pipeline is ready!
echo.
echo ============================================
echo   ALL SERVICES ARE RUNNING!
echo ============================================
echo.
echo   SERVICE URLS:
echo   - Kibana Dashboard:   http://localhost:5601
echo   - Spark Master UI:    http://localhost:8080
echo   - ElasticSearch:      http://localhost:9200
echo.
echo   NOTE: Your previous tweets are PRESERVED!
echo         New tweets will be added to existing data.
echo.
echo ============================================
echo.
echo Opening Kibana in your browser...
start http://localhost:5601

echo.
echo ============================================
echo   TWEET SIMULATOR
echo ============================================
echo.
echo Starting Tweet Simulator...
echo Tweets are sent directly to ElasticSearch (no Spark needed)
echo.
echo Press Ctrl+C to stop the simulator
echo.
python src/ingestion/tweet_simulator.py

echo.
echo ============================================
echo   Simulator stopped.
echo.
echo   Your tweets are saved in ElasticSearch!
echo   View them at: http://localhost:5601
echo.
echo   To stop all containers, run: docker-compose down
echo   Or double-click: stop_pipeline.bat
echo ============================================
pause
