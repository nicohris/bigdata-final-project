"""
Twitter Stream Producer for Kafka

This module connects to the Twitter Streaming API and publishes
raw tweets to a Kafka topic for downstream processing.
"""

import json
import os
from datetime import datetime
from kafka import KafkaProducer
import tweepy


class TwitterKafkaProducer(tweepy.StreamingClient):
    """
    Custom Twitter streaming client that publishes tweets to Kafka.
    """
    
    def __init__(self, bearer_token: str, kafka_bootstrap_servers: str, topic: str):
        """
        Initialize the Twitter stream with Kafka producer.
        
        Args:
            bearer_token: Twitter API v2 bearer token
            kafka_bootstrap_servers: Kafka broker addresses
            topic: Kafka topic to publish tweets to
        """
        super().__init__(bearer_token, wait_on_rate_limit=True)
        
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3,
            compression_type='snappy'
        )
        
        print(f"[{datetime.now()}] Kafka producer initialized for topic: {topic}")
    
    def on_tweet(self, tweet):
        """
        Called when a new tweet is received.
        Publishes the tweet data to Kafka.
        """
        try:
            tweet_data = {
                'id': tweet.id,
                'text': tweet.text,
                'author_id': tweet.author_id,
                'created_at': str(tweet.created_at) if tweet.created_at else None,
                'ingested_at': datetime.utcnow().isoformat(),
                'geo': tweet.geo if hasattr(tweet, 'geo') else None,
                'entities': {
                    'hashtags': [ht['tag'] for ht in (tweet.entities or {}).get('hashtags', [])],
                    'mentions': [m['username'] for m in (tweet.entities or {}).get('mentions', [])]
                }
            }
            
            # Send to Kafka
            future = self.producer.send(self.topic, value=tweet_data)
            future.get(timeout=10)  # Block until sent
            
            print(f"[{datetime.now()}] Published tweet {tweet.id}: {tweet.text[:50]}...")
            
        except Exception as e:
            print(f"[{datetime.now()}] Error publishing tweet: {e}")
    
    def on_error(self, status_code):
        """
        Handle stream errors.
        """
        print(f"[{datetime.now()}] Stream error: {status_code}")
        if status_code == 420:
            # Rate limited - disconnect and wait
            print("Rate limited. Disconnecting...")
            return False
        return True
    
    def on_disconnect(self):
        """
        Called when the stream is disconnected.
        """
        print(f"[{datetime.now()}] Stream disconnected")
        self.producer.flush()
        self.producer.close()


def setup_stream_rules(stream: TwitterKafkaProducer, keywords: list, reset: bool = True):
    """
    Configure the stream filter rules.
    
    Args:
        stream: TwitterKafkaProducer instance
        keywords: List of keywords/hashtags to track
        reset: If True, delete existing rules before adding new ones
    """
    # Get existing rules
    existing_rules = stream.get_rules()
    
    if reset and existing_rules.data:
        # Delete existing rules
        rule_ids = [rule.id for rule in existing_rules.data]
        stream.delete_rules(rule_ids)
        print(f"Deleted {len(rule_ids)} existing rules")
    
    # Build rule query
    query_parts = [f'({kw})' for kw in keywords]
    query = ' OR '.join(query_parts) + ' lang:en -is:retweet'
    
    # Add new rule
    stream.add_rules(tweepy.StreamRule(query))
    print(f"Added rule: {query}")


def main():
    """
    Main entry point for the Twitter producer.
    """
    # Configuration from environment variables
    BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')
    KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'tweets_raw')
    KEYWORDS = os.getenv('TRACK_KEYWORDS', 'TechnoGadget,TechnoPhone').split(',')
    
    if not BEARER_TOKEN:
        raise ValueError("TWITTER_BEARER_TOKEN environment variable is required")
    
    print("=" * 60)
    print("Twitter to Kafka Producer")
    print("=" * 60)
    print(f"Kafka servers: {KAFKA_SERVERS}")
    print(f"Kafka topic: {KAFKA_TOPIC}")
    print(f"Tracking keywords: {KEYWORDS}")
    print("=" * 60)
    
    # Initialize stream
    stream = TwitterKafkaProducer(
        bearer_token=BEARER_TOKEN,
        kafka_bootstrap_servers=KAFKA_SERVERS,
        topic=KAFKA_TOPIC
    )
    
    # Setup rules
    setup_stream_rules(stream, KEYWORDS)
    
    # Start streaming
    print("Starting stream...")
    stream.filter(
        tweet_fields=['created_at', 'author_id', 'geo', 'entities'],
        user_fields=['username', 'name', 'public_metrics'],
        expansions=['author_id']
    )


if __name__ == '__main__':
    main()
