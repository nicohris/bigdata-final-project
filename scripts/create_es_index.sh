#!/bin/bash
# ============================================
# ElasticSearch Index Creation Script
# ============================================
# This script creates the brand_tweets index with
# optimized mappings for sentiment analysis data.
# ============================================

ES_HOST="${ELASTICSEARCH_HOST:-localhost:9200}"
INDEX_NAME="${INDEX_NAME:-brand_tweets}"

echo "============================================"
echo "Creating ElasticSearch Index"
echo "============================================"
echo "Host: $ES_HOST"
echo "Index: $INDEX_NAME"
echo "============================================"

# Check if index exists
if curl -s -o /dev/null -w "%{http_code}" "http://$ES_HOST/$INDEX_NAME" | grep -q "200"; then
    echo "Index '$INDEX_NAME' already exists."
    read -p "Delete and recreate? (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
        echo "Deleting index..."
        curl -X DELETE "http://$ES_HOST/$INDEX_NAME"
        echo ""
    else
        echo "Aborting."
        exit 0
    fi
fi

# Create index with mappings
echo "Creating index with mappings..."
curl -X PUT "http://$ES_HOST/$INDEX_NAME" -H "Content-Type: application/json" -d '
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "refresh_interval": "5s",
    "analysis": {
      "analyzer": {
        "tweet_analyzer": {
          "type": "custom",
          "tokenizer": "standard",
          "filter": ["lowercase", "stop", "snowball"]
        }
      }
    }
  },
  "mappings": {
    "properties": {
      "tweet_id": {
        "type": "keyword"
      },
      "original_text": {
        "type": "text",
        "analyzer": "tweet_analyzer",
        "fields": {
          "raw": {
            "type": "keyword"
          }
        }
      },
      "cleaned_text": {
        "type": "text",
        "analyzer": "tweet_analyzer"
      },
      "sentiment_label": {
        "type": "keyword"
      },
      "sentiment_score": {
        "type": "float"
      },
      "hashtags": {
        "type": "keyword"
      },
      "mentions": {
        "type": "keyword"
      },
      "keywords": {
        "type": "keyword"
      },
      "author_id": {
        "type": "keyword"
      },
      "author_username": {
        "type": "keyword"
      },
      "author_followers": {
        "type": "integer"
      },
      "is_complaint": {
        "type": "boolean"
      },
      "priority": {
        "type": "keyword"
      },
      "location": {
        "type": "geo_point"
      },
      "created_at": {
        "type": "date"
      },
      "processed_at": {
        "type": "date"
      }
    }
  }
}'

echo ""
echo "============================================"
echo "Index creation complete!"
echo "============================================"

# Verify index was created
echo "Verifying index..."
curl -s "http://$ES_HOST/$INDEX_NAME/_mapping" | python3 -m json.tool 2>/dev/null || echo "Index verified."
echo ""
echo "Done!"
