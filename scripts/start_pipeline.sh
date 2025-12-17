#!/bin/bash
# ============================================
# Big Data Pipeline Startup Script
# ============================================
# This script starts all components of the
# brand monitoring pipeline in the correct order.
# ============================================

set -e

echo "============================================"
echo "Starting Big Data Pipeline"
echo "============================================"

# Navigate to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "Project directory: $PROJECT_DIR"

# Start Docker containers
echo ""
echo "[1/5] Starting Docker containers..."
docker-compose up -d

# Wait for services to be healthy
echo ""
echo "[2/5] Waiting for services to start..."

# Wait for Kafka
echo "  - Waiting for Kafka..."
until docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list &>/dev/null; do
    sleep 2
done
echo "  - Kafka is ready!"

# Wait for ElasticSearch
echo "  - Waiting for ElasticSearch..."
until curl -s http://localhost:9200/_cluster/health | grep -q '"status":"green\|yellow"'; do
    sleep 2
done
echo "  - ElasticSearch is ready!"

# Wait for Kibana
echo "  - Waiting for Kibana..."
until curl -s http://localhost:5601/api/status | grep -q "available"; do
    sleep 2
done
echo "  - Kibana is ready!"

# Create Kafka topics
echo ""
echo "[3/5] Creating Kafka topics..."
docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --if-not-exists \
    --topic tweets_raw \
    --partitions 6 \
    --replication-factor 1

docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --if-not-exists \
    --topic tweets_processed \
    --partitions 6 \
    --replication-factor 1

docker exec kafka kafka-topics --bootstrap-server localhost:9092 \
    --create --if-not-exists \
    --topic tweets_alerts \
    --partitions 2 \
    --replication-factor 1

echo "  - Topics created!"

# Create ElasticSearch index
echo ""
echo "[4/5] Creating ElasticSearch index..."
bash "$SCRIPT_DIR/create_es_index.sh"

# Print status
echo ""
echo "[5/5] Pipeline ready!"
echo "============================================"
echo ""
echo "Service URLs:"
echo "  - Spark Master UI:    http://localhost:8080"
echo "  - Spark Worker UI:    http://localhost:8081"
echo "  - ElasticSearch:      http://localhost:9200"
echo "  - Kibana:             http://localhost:5601"
echo ""
echo "Kafka Topics:"
docker exec kafka kafka-topics --bootstrap-server localhost:9092 --list
echo ""
echo "============================================"
echo "To start the Twitter producer, run:"
echo "  export TWITTER_BEARER_TOKEN='your-token'"
echo "  python src/ingestion/twitter_producer.py"
echo ""
echo "To start the Spark processor, run:"
echo "  docker exec spark-master spark-submit \\"
echo "    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \\"
echo "    /opt/spark-apps/processing/spark_processor.py"
echo "============================================"
