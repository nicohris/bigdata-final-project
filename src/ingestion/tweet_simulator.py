"""
Tweet Simulator - Generates realistic fake tweets for pipeline testing.

This module simulates the Twitter API by generating realistic tweets
with varying sentiments and publishing them to Kafka AND ElasticSearch.
This allows testing the full pipeline without Twitter API access.

Usage:
    python tweet_simulator.py
"""

import json
import random
import time
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer
from elasticsearch import Elasticsearch
from textblob import TextBlob


# ============================================
# SAMPLE DATA FOR REALISTIC TWEET GENERATION
# ============================================

POSITIVE_TEMPLATES = [
    "Just got my new #TechnoPhone and I'm absolutely in love with it! 🔥 @TechnoGadget",
    "The battery life on #TechnoPhone is incredible! Lasted all day with heavy use 📱",
    "Best phone purchase I've ever made! #TechnoPhone is amazing @TechnoGadget ❤️",
    "Switched from iPhone to #TechnoPhone - no regrets! The camera is stunning 📸",
    "Customer service at @TechnoGadget was super helpful! Issue resolved in minutes 👏",
    "#TechnoPhone software update is smooth as butter! Great job @TechnoGadget 🚀",
    "Everyone asking about my new #TechnoPhone - it's that beautiful! #tech #innovation",
    "The screen quality on #TechnoPhone is mind-blowing! Best display ever 🎉",
    "3 months with #TechnoPhone and still impressed every day @TechnoGadget",
    "Just recommended #TechnoPhone to all my friends! Worth every penny 💯",
]

NEGATIVE_TEMPLATES = [
    "@TechnoGadget your customer service is terrible! Still waiting for my refund #frustrated",
    "My #TechnoPhone keeps crashing! This is unacceptable @TechnoGadget 😡",
    "#TechnoPhone battery dies in 4 hours. What a disappointment @TechnoGadget",
    "Worst purchase ever! #TechnoPhone camera quality is horrible in low light 👎",
    "Been on hold with @TechnoGadget support for 2 hours. Never buying again! #badservice",
    "#TechnoPhone overheats constantly! Regret switching from Samsung @TechnoGadget",
    "Screen cracked after 1 week. Build quality is garbage #TechnoPhone @TechnoGadget",
    "Why does #TechnoPhone have so many bugs? Fix your software @TechnoGadget! 🐛",
    "@TechnoGadget shipped wrong color TWICE. Incompetent company #fail",
    "Returning my #TechnoPhone tomorrow. Constant connectivity issues @TechnoGadget",
]

NEUTRAL_TEMPLATES = [
    "Thinking about getting the new #TechnoPhone. Any thoughts? @TechnoGadget",
    "Just saw an ad for #TechnoPhone. Looks interesting 🤔",
    "#TechnoPhone or iPhone? Help me decide! @TechnoGadget",
    "Anyone know when #TechnoPhone will be available in stores? @TechnoGadget",
    "Comparing specs between #TechnoPhone and competitors today",
    "#TechnoPhone seems okay. Nothing special though @TechnoGadget",
    "Reading reviews about #TechnoPhone. Mixed feelings so far",
    "Is #TechnoPhone worth the price? @TechnoGadget",
    "Saw someone with #TechnoPhone on the subway today",
    "#TechnoPhone announcement coming next week apparently @TechnoGadget",
]

USERNAMES = [
    "tech_lover_92", "sarah_reviews", "mike_gadgets", "emma_digital",
    "alex_mobile", "chris_tech", "jordan_phones", "taylor_geek",
    "sam_innovation", "casey_devices", "morgan_smart", "riley_apps",
    "jamie_connected", "drew_future", "pat_wireless", "kim_silicon"
]

HASHTAGS = [
    "TechnoPhone", "TechnoGadget", "smartphone", "tech", "innovation",
    "mobile", "gadgets", "phonelife", "technology", "newphone"
]


def analyze_sentiment(text: str) -> tuple:
    """
    Analyze sentiment of text using TextBlob.
    
    Returns:
        Tuple of (label, score)
    """
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    
    if polarity > 0.1:
        return ("positive", polarity)
    elif polarity < -0.1:
        return ("negative", polarity)
    else:
        return ("neutral", polarity)


def generate_fake_tweet(tweet_id: int) -> dict:
    """
    Generate a realistic fake tweet with random sentiment.
    
    Args:
        tweet_id: Unique identifier for the tweet
        
    Returns:
        Tweet data dictionary matching Twitter API format
    """
    # Randomly select sentiment (weighted towards positive for realism)
    sentiment_roll = random.random()
    if sentiment_roll < 0.5:  # 50% positive
        text = random.choice(POSITIVE_TEMPLATES)
    elif sentiment_roll < 0.75:  # 25% negative  
        text = random.choice(NEGATIVE_TEMPLATES)
    else:  # 25% neutral
        text = random.choice(NEUTRAL_TEMPLATES)
    
    # Generate random user data
    username = random.choice(USERNAMES)
    followers = random.randint(50, 100000)
    
    # Extract hashtags from text
    hashtags = []
    for word in text.split():
        if word.startswith('#'):
            tag = word[1:].rstrip('.,!?')
            hashtags.append({"start": text.index(word), "end": text.index(word) + len(word), "tag": tag})
    
    # Get current time
    now = datetime.now(timezone.utc)
    
    # Generate unique tweet ID using timestamp + random (prevents overwrites)
    unique_id = f"{int(now.timestamp() * 1000000)}{random.randint(1000, 9999)}"
    
    # Build tweet structure matching Twitter API v2 format
    tweet = {
        "data": {
            "id": unique_id,
            "text": text,
            "author_id": str(random.randint(1000000000, 9999999999)),
            "created_at": now.isoformat().replace('+00:00', 'Z'),
            "entities": {
                "hashtags": hashtags,
                "mentions": [{"username": "TechnoGadget"}] if "@TechnoGadget" in text else []
            }
        },
        "includes": {
            "users": [{
                "id": str(random.randint(1000000000, 9999999999)),
                "name": username.replace("_", " ").title(),
                "username": username,
                "public_metrics": {
                    "followers_count": followers,
                    "following_count": random.randint(100, 2000)
                }
            }]
        }
    }
    
    return tweet


def process_tweet_for_elastic(raw_tweet: dict) -> dict:
    """
    Process raw tweet data into ElasticSearch document format.
    
    Args:
        raw_tweet: Raw tweet from simulator
        
    Returns:
        Processed document ready for ElasticSearch
    """
    data = raw_tweet["data"]
    user = raw_tweet["includes"]["users"][0]
    
    text = data["text"]
    sentiment_label, sentiment_score = analyze_sentiment(text)
    
    # Extract hashtags
    hashtags = [h["tag"].lower() for h in data["entities"].get("hashtags", [])]
    
    # Extract mentions
    mentions = [m["username"].lower() for m in data["entities"].get("mentions", [])]
    
    # Determine if complaint
    is_complaint = sentiment_label == "negative" and any(
        word in text.lower() for word in ["terrible", "worst", "frustrated", "disappointed", "garbage", "fail"]
    )
    
    # Determine priority
    if sentiment_score < -0.5:
        priority = "high"
    elif sentiment_score < -0.2:
        priority = "medium"
    else:
        priority = "low"
    
    return {
        "tweet_id": data["id"],
        "original_text": text,
        "cleaned_text": text.lower().replace("#", "").replace("@", ""),
        "sentiment_label": sentiment_label,
        "sentiment_score": round(sentiment_score, 3),
        "hashtags": hashtags,
        "mentions": mentions,
        "author_id": user["id"],
        "author_username": user["username"],
        "author_followers": user["public_metrics"]["followers_count"],
        "is_complaint": is_complaint,
        "priority": priority,
        "created_at": data["created_at"],
        "processed_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    }


def create_kafka_producer(bootstrap_servers: str) -> KafkaProducer:
    """
    Create and configure Kafka producer.
    
    Args:
        bootstrap_servers: Kafka broker addresses
        
    Returns:
        Configured KafkaProducer instance
    """
    return KafkaProducer(
        bootstrap_servers=bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all'
    )


def create_es_index(es: Elasticsearch, index_name: str):
    """Create ElasticSearch index if it doesn't exist."""
    
    if es.indices.exists(index=index_name):
        return  # Index already exists
    
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
                "is_complaint": {"type": "boolean"},
                "priority": {"type": "keyword"},
                "created_at": {"type": "date"},
                "processed_at": {"type": "date"}
            }
        }
    }
    
    es.indices.create(index=index_name, body=mapping)
    print(f"✅ Created ElasticSearch index '{index_name}'")


def run_simulator(kafka_servers: str = "localhost:29092",
                  topic: str = "tweets_raw",
                  es_host: str = "http://localhost:9200",
                  es_index: str = "brand_tweets",
                  tweets_per_minute: int = 30,
                  duration_minutes: int = 5):
    """
    Run the tweet simulator, publishing fake tweets to Kafka AND ElasticSearch.
    
    Args:
        kafka_servers: Kafka bootstrap servers
        topic: Kafka topic to publish to
        es_host: ElasticSearch host URL
        es_index: ElasticSearch index name
        tweets_per_minute: Rate of tweet generation
        duration_minutes: How long to run (0 = forever)
    """
    print("=" * 60)
    print("🐦 Tweet Simulator - Fake Data Generator")
    print("=" * 60)
    print(f"Kafka servers: {kafka_servers}")
    print(f"Kafka topic: {topic}")
    print(f"ElasticSearch: {es_host}")
    print(f"ES Index: {es_index}")
    print(f"Rate: {tweets_per_minute} tweets/minute")
    print(f"Duration: {'∞' if duration_minutes == 0 else f'{duration_minutes} minutes'}")
    print("=" * 60)
    print()
    
    # Connect to Kafka
    kafka_connected = False
    try:
        producer = create_kafka_producer(kafka_servers)
        print("✅ Connected to Kafka!")
        kafka_connected = True
    except Exception as e:
        print(f"⚠️ Kafka not available: {e}")
        print("   Tweets will only be sent to ElasticSearch")
        producer = None
    
    # Connect to ElasticSearch
    es_connected = False
    try:
        es = Elasticsearch([es_host])
        es.info()
        print("✅ Connected to ElasticSearch!")
        create_es_index(es, es_index)
        es_connected = True
    except Exception as e:
        print(f"⚠️ ElasticSearch not available: {e}")
        es = None
    
    if not kafka_connected and not es_connected:
        print("\n❌ No backends available! Make sure Docker containers are running:")
        print("   docker-compose up -d")
        return
    
    # Calculate delay between tweets
    delay = 60.0 / tweets_per_minute
    
    tweet_count = 0
    es_count = 0
    kafka_count = 0
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60) if duration_minutes > 0 else float('inf')
    
    print("\n📤 Sending tweets...\n")
    
    try:
        while time.time() < end_time:
            # Generate tweet
            tweet = generate_fake_tweet(tweet_count)
            
            # Send to Kafka if available
            if producer:
                try:
                    future = producer.send(topic, value=tweet["data"])
                    future.get(timeout=10)
                    kafka_count += 1
                except Exception as e:
                    print(f"⚠️ Kafka error: {e}")
            
            # Send to ElasticSearch if available
            if es:
                try:
                    doc = process_tweet_for_elastic(tweet)
                    es.index(index=es_index, id=doc["tweet_id"], document=doc)
                    es_count += 1
                except Exception as e:
                    print(f"⚠️ ES error: {e}")
            
            # Log progress
            sentiment_indicator = "🟢" if "love" in tweet["data"]["text"].lower() or "amazing" in tweet["data"]["text"].lower() else \
                                  "🔴" if "terrible" in tweet["data"]["text"].lower() or "worst" in tweet["data"]["text"].lower() else "🟡"
            
            print(f"{sentiment_indicator} Tweet #{tweet_count + 1}: {tweet['data']['text'][:55]}...")
            
            tweet_count += 1
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulator stopped by user")
    finally:
        if producer:
            producer.flush()
            producer.close()
        
    elapsed = time.time() - start_time
    print(f"\n✅ Simulation complete!")
    print(f"   Total tweets generated: {tweet_count}")
    print(f"   Sent to Kafka: {kafka_count}")
    print(f"   Sent to ElasticSearch: {es_count}")
    print(f"   Duration: {elapsed:.1f} seconds")
    print(f"   Rate: {tweet_count / elapsed * 60:.1f} tweets/minute")
    print(f"\n🔗 View your data in Kibana: http://localhost:5601")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Tweet Simulator for Big Data Pipeline")
    parser.add_argument("--kafka", default="localhost:29092", help="Kafka bootstrap servers")
    parser.add_argument("--topic", default="tweets_raw", help="Kafka topic")
    parser.add_argument("--es", default="http://localhost:9200", help="ElasticSearch host")
    parser.add_argument("--index", default="brand_tweets", help="ElasticSearch index")
    parser.add_argument("--rate", type=int, default=30, help="Tweets per minute")
    parser.add_argument("--duration", type=int, default=5, help="Duration in minutes (0 = forever)")
    
    args = parser.parse_args()
    
    run_simulator(
        kafka_servers=args.kafka,
        topic=args.topic,
        es_host=args.es,
        es_index=args.index,
        tweets_per_minute=args.rate,
        duration_minutes=args.duration
    )
