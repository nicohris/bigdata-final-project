"""
Direct ElasticSearch Loader - Load sample data without Kafka/Spark.

This script loads processed tweets directly into ElasticSearch,
bypassing Kafka and Spark. Useful for testing Kibana dashboards
quickly.

Usage:
    python load_sample_data.py
"""

import json
import random
from datetime import datetime, timedelta
from elasticsearch import Elasticsearch


# Sample processed tweets with realistic data
SAMPLE_TWEETS = [
    {
        "tweet_id": "1869712345678901234",
        "original_text": "Just got my new #TechnoPhone and the battery life is AMAZING! Best purchase ever @TechnoGadget 🔥",
        "cleaned_text": "just got my new technophone and the battery life is amazing best purchase ever",
        "sentiment_label": "positive",
        "sentiment_score": 0.89,
        "hashtags": ["technophone"],
        "mentions": ["technogadget"],
        "author_id": "9876543210",
        "author_username": "sarahtech",
        "author_followers": 1523,
        "keywords": ["battery life", "purchase", "amazing"],
        "is_complaint": False,
        "priority": "low"
    },
    {
        "tweet_id": "1869712345678901235",
        "original_text": "@TechnoGadget Your customer service is terrible! Been waiting 2 weeks for my refund. #frustrated #badservice",
        "cleaned_text": "your customer service is terrible been waiting 2 weeks for my refund",
        "sentiment_label": "negative",
        "sentiment_score": -0.76,
        "hashtags": ["frustrated", "badservice"],
        "mentions": ["technogadget"],
        "author_id": "1122334455",
        "author_username": "mikej_tech",
        "author_followers": 342,
        "keywords": ["customer service", "refund", "waiting"],
        "is_complaint": True,
        "priority": "high"
    },
    {
        "tweet_id": "1869712345678901236",
        "original_text": "The camera on the #TechnoPhone is honestly meh. Nothing special compared to iPhone.",
        "cleaned_text": "the camera on the technophone is honestly meh nothing special",
        "sentiment_label": "negative",
        "sentiment_score": -0.34,
        "hashtags": ["technophone"],
        "mentions": ["technogadget"],
        "author_id": "5566778899",
        "author_username": "photopro_alex",
        "author_followers": 15234,
        "keywords": ["camera", "iphone"],
        "is_complaint": False,
        "priority": "medium"
    },
    {
        "tweet_id": "1869712345678901237",
        "original_text": "Switched from Samsung to #TechnoPhone - no regrets! The software is so smooth 🚀 #innovation",
        "cleaned_text": "switched from samsung to technophone no regrets the software is so smooth",
        "sentiment_label": "positive",
        "sentiment_score": 0.72,
        "hashtags": ["technophone", "innovation"],
        "mentions": [],
        "author_id": "3344556677",
        "author_username": "lisareviews",
        "author_followers": 89234,
        "keywords": ["samsung", "software", "smooth"],
        "is_complaint": False,
        "priority": "low"
    },
    {
        "tweet_id": "1869712345678901238",
        "original_text": "Anyone else having issues with #TechnoPhone overheating? Mine gets really hot when gaming 🎮🔥",
        "cleaned_text": "anyone else having issues with technophone overheating mine gets really hot when gaming",
        "sentiment_label": "negative",
        "sentiment_score": -0.45,
        "hashtags": ["technophone"],
        "mentions": ["technogadget"],
        "author_id": "7788990011",
        "author_username": "gamer_dude_99",
        "author_followers": 2341,
        "keywords": ["overheating", "gaming", "issues"],
        "is_complaint": True,
        "priority": "medium"
    }
]

# Additional templates for generating more variety
POSITIVE_TEXTS = [
    ("Love my #TechnoPhone! Best decision ever @TechnoGadget", 0.85),
    ("#TechnoPhone camera quality is absolutely stunning! 📸", 0.78),
    ("@TechnoGadget thank you for the quick delivery! Impressed 👏", 0.65),
    ("The new update made #TechnoPhone even better! Great work", 0.72),
    ("3 months with #TechnoPhone and still loving it! #satisfied", 0.81),
]

NEGATIVE_TEXTS = [
    ("@TechnoGadget screen cracked after 1 week! Terrible quality", -0.82),
    ("#TechnoPhone keeps freezing! So frustrated right now 😤", -0.68),
    ("Worst purchase ever. #TechnoPhone is garbage @TechnoGadget", -0.91),
    ("Still waiting for support response @TechnoGadget #badservice", -0.55),
    ("Battery drains in 3 hours! #TechnoPhone is a joke", -0.73),
]

NEUTRAL_TEXTS = [
    ("Thinking about getting #TechnoPhone. Any reviews?", 0.05),
    ("Just saw the new #TechnoPhone ad. Looks okay 🤔", 0.12),
    ("#TechnoPhone vs iPhone - still deciding @TechnoGadget", -0.08),
    ("Anyone know when #TechnoPhone will be on sale?", 0.02),
    ("Reading about #TechnoPhone features today", 0.0),
]


def generate_bulk_tweets(count: int = 100):
    """Generate multiple tweets with varied timestamps over past 7 days."""
    tweets = []
    base_time = datetime.utcnow()
    
    for i in range(count):
        # Random time in past 7 days
        random_offset = timedelta(
            days=random.randint(0, 6),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
            seconds=random.randint(0, 59)
        )
        timestamp = (base_time - random_offset).isoformat() + "Z"
        
        # Select sentiment category
        roll = random.random()
        if roll < 0.5:  # 50% positive
            text, score = random.choice(POSITIVE_TEXTS)
            label = "positive"
        elif roll < 0.75:  # 25% negative
            text, score = random.choice(NEGATIVE_TEXTS)
            label = "negative"
        else:  # 25% neutral
            text, score = random.choice(NEUTRAL_TEXTS)
            label = "neutral"
        
        tweet = {
            "tweet_id": str(1869700000000000000 + i),
            "original_text": text,
            "cleaned_text": text.lower().replace("#", "").replace("@", ""),
            "sentiment_label": label,
            "sentiment_score": score + random.uniform(-0.1, 0.1),
            "hashtags": ["technophone"] if "#TechnoPhone" in text else [],
            "mentions": ["technogadget"] if "@TechnoGadget" in text else [],
            "author_id": str(random.randint(1000000000, 9999999999)),
            "author_username": f"user_{random.randint(1000, 9999)}",
            "author_followers": random.randint(50, 50000),
            "is_complaint": label == "negative" and random.random() > 0.3,
            "priority": "high" if score < -0.7 else "medium" if score < -0.3 else "low",
            "created_at": timestamp,
            "processed_at": timestamp
        }
        tweets.append(tweet)
    
    return tweets


def create_index(es: Elasticsearch, index_name: str):
    """Create ElasticSearch index with proper mappings."""
    
    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "1s"
        },
        "mappings": {
            "properties": {
                "tweet_id": {"type": "keyword"},
                "original_text": {"type": "text"},
                "cleaned_text": {"type": "text"},
                "sentiment_label": {"type": "keyword"},
                "sentiment_score": {"type": "float"},
                "hashtags": {"type": "keyword"},
                "mentions": {"type": "keyword"},
                "author_id": {"type": "keyword"},
                "author_username": {"type": "keyword"},
                "author_followers": {"type": "integer"},
                "keywords": {"type": "keyword"},
                "is_complaint": {"type": "boolean"},
                "priority": {"type": "keyword"},
                "created_at": {"type": "date"},
                "processed_at": {"type": "date"}
            }
        }
    }
    
    # Only create if doesn't exist (preserve existing data)
    if es.indices.exists(index=index_name):
        print(f"✅ Index '{index_name}' already exists - keeping existing data")
        return
    
    # Create new index
    es.indices.create(index=index_name, body=mapping)
    print(f"✅ Created new index '{index_name}'")


def load_data(es: Elasticsearch, index_name: str, tweets: list):
    """Bulk load tweets into ElasticSearch."""
    
    from elasticsearch.helpers import bulk
    
    actions = [
        {
            "_index": index_name,
            "_id": tweet["tweet_id"],
            "_source": tweet
        }
        for tweet in tweets
    ]
    
    success, errors = bulk(es, actions, raise_on_error=False)
    print(f"✅ Loaded {success} documents")
    if errors:
        print(f"⚠️ {len(errors)} errors occurred")


def main():
    """Main entry point."""
    
    print("=" * 60)
    print("📊 ElasticSearch Data Loader")
    print("=" * 60)
    
    ES_HOST = "http://localhost:9200"
    INDEX_NAME = "brand_tweets"
    TWEET_COUNT = 200
    
    print(f"ElasticSearch: {ES_HOST}")
    print(f"Index: {INDEX_NAME}")
    print("=" * 60)
    
    # Connect to ElasticSearch
    try:
        es = Elasticsearch([ES_HOST])
        info = es.info()
        print(f"✅ Connected to ElasticSearch {info['version']['number']}")
    except Exception as e:
        print(f"❌ Failed to connect to ElasticSearch: {e}")
        print("\n💡 Make sure Docker containers are running:")
        print("   docker-compose up -d")
        return
    
    # Check if index exists and has data
    if es.indices.exists(index=INDEX_NAME):
        count = es.count(index=INDEX_NAME)["count"]
        if count > 0:
            print(f"\n✅ Index '{INDEX_NAME}' already has {count} tweets")
            print("   Skipping sample data load to preserve existing data")
            print("\n� To reset data, run: python src/utils/reset_data.py")
            print("=" * 60)
            return
        else:
            print(f"\n�📋 Index '{INDEX_NAME}' exists but is empty")
    else:
        print("\n📋 Creating index...")
        create_index(es, INDEX_NAME)
    
    # Generate and load data only if index is new/empty
    print(f"\n🐦 Generating {TWEET_COUNT} sample tweets...")
    tweets = SAMPLE_TWEETS + generate_bulk_tweets(TWEET_COUNT - len(SAMPLE_TWEETS))
    
    print(f"\n📤 Loading data into ElasticSearch...")
    load_data(es, INDEX_NAME, tweets)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Data loaded successfully!")
    print("=" * 60)
    print("\n🔗 Next steps:")
    print("   1. Open Kibana: http://localhost:5601")
    print("   2. Go to Analytics → Discover to see data")
    print("   3. Create dashboards in Analytics → Dashboard")
    print("=" * 60)


if __name__ == "__main__":
    main()
