"""
Spark Streaming Processor for Tweet Sentiment Analysis

This module consumes raw tweets from Kafka, performs text cleaning,
sentiment analysis, and feature extraction, then writes enriched
documents to ElasticSearch.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    from_json, col, udf, current_timestamp, lower, regexp_replace, trim
)
from pyspark.sql.types import (
    StructType, StructField, StringType, ArrayType, FloatType, BooleanType
)
import re
from textblob import TextBlob


# ============================================
# SCHEMA DEFINITIONS
# ============================================

# Schema for incoming raw tweets from Kafka
RAW_TWEET_SCHEMA = StructType([
    StructField("id", StringType(), True),
    StructField("text", StringType(), True),
    StructField("author_id", StringType(), True),
    StructField("created_at", StringType(), True),
    StructField("ingested_at", StringType(), True),
    StructField("geo", StringType(), True),
    StructField("entities", StructType([
        StructField("hashtags", ArrayType(StringType()), True),
        StructField("mentions", ArrayType(StringType()), True)
    ]), True)
])

# Schema for sentiment output
SENTIMENT_SCHEMA = StructType([
    StructField("label", StringType(), True),
    StructField("score", FloatType(), True)
])


# ============================================
# TEXT PROCESSING FUNCTIONS
# ============================================

def clean_text(text: str) -> str:
    """
    Clean tweet text by removing URLs, mentions, and special characters.
    
    Args:
        text: Raw tweet text
    
    Returns:
        Cleaned and normalized text
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove mentions (@ handles)
    text = re.sub(r'@\w+', '', text)
    
    # Remove hashtag symbols (keep the word)
    text = re.sub(r'#', '', text)
    
    # Remove special characters except spaces and basic punctuation
    text = re.sub(r'[^\w\s.,!?]', '', text)
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Lowercase
    return text.lower().strip()


def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of cleaned text using TextBlob.
    
    Args:
        text: Cleaned tweet text
    
    Returns:
        Dictionary with sentiment label and score
    """
    if not text:
        return {"label": "neutral", "score": 0.0}
    
    try:
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        
        if polarity > 0.1:
            label = "positive"
        elif polarity < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return {"label": label, "score": float(polarity)}
    
    except Exception:
        return {"label": "neutral", "score": 0.0}


def extract_keywords(text: str) -> list:
    """
    Extract important keywords from text using noun phrase extraction.
    
    Args:
        text: Cleaned tweet text
    
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    try:
        blob = TextBlob(text)
        # Extract noun phrases as keywords
        keywords = [phrase.lower() for phrase in blob.noun_phrases if len(phrase) > 2]
        return keywords[:5]  # Limit to 5 keywords
    except Exception:
        return []


def is_complaint(sentiment_score: float, text: str) -> bool:
    """
    Determine if tweet is a complaint based on sentiment and keywords.
    
    Args:
        sentiment_score: Sentiment polarity score
        text: Cleaned tweet text
    
    Returns:
        True if tweet appears to be a complaint
    """
    complaint_keywords = [
        'terrible', 'awful', 'worst', 'hate', 'broken', 'fail',
        'refund', 'scam', 'disappointed', 'frustrated', 'waiting',
        'customer service', 'support', 'help', 'issue', 'problem'
    ]
    
    if sentiment_score < -0.3:
        return True
    
    text_lower = text.lower() if text else ""
    for keyword in complaint_keywords:
        if keyword in text_lower:
            return True
    
    return False


def get_priority(sentiment_score: float, followers_count: int) -> str:
    """
    Determine priority level based on sentiment and author influence.
    
    Args:
        sentiment_score: Sentiment polarity score
        followers_count: Number of followers the author has
    
    Returns:
        Priority level: 'high', 'medium', or 'low'
    """
    if sentiment_score < -0.5 and followers_count > 10000:
        return "high"
    elif sentiment_score < -0.3 or followers_count > 5000:
        return "medium"
    else:
        return "low"


# ============================================
# UDF DEFINITIONS
# ============================================

# Register UDFs for Spark
clean_text_udf = udf(clean_text, StringType())
analyze_sentiment_udf = udf(analyze_sentiment, SENTIMENT_SCHEMA)
extract_keywords_udf = udf(extract_keywords, ArrayType(StringType()))
is_complaint_udf = udf(is_complaint, BooleanType())
get_priority_udf = udf(get_priority, StringType())


# ============================================
# SPARK STREAMING APPLICATION
# ============================================

def create_spark_session():
    """
    Create and configure Spark session with required packages.
    """
    return SparkSession.builder \
        .appName("TweetSentimentProcessor") \
        .config("spark.jars.packages", 
                "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                "org.elasticsearch:elasticsearch-spark-30_2.12:8.11.0") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
        .getOrCreate()


def process_tweets(spark: SparkSession, 
                  kafka_servers: str,
                  input_topic: str,
                  es_nodes: str,
                  es_index: str):
    """
    Main processing pipeline for tweet sentiment analysis.
    
    Args:
        spark: SparkSession
        kafka_servers: Kafka bootstrap servers
        input_topic: Kafka topic to consume from
        es_nodes: ElasticSearch nodes
        es_index: ElasticSearch index to write to
    """
    
    print("=" * 60)
    print("Tweet Sentiment Processor")
    print("=" * 60)
    print(f"Kafka servers: {kafka_servers}")
    print(f"Input topic: {input_topic}")
    print(f"ElasticSearch nodes: {es_nodes}")
    print(f"ElasticSearch index: {es_index}")
    print("=" * 60)
    
    # Read from Kafka
    raw_stream = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_servers) \
        .option("subscribe", input_topic) \
        .option("startingOffsets", "latest") \
        .option("failOnDataLoss", "false") \
        .load()
    
    # Parse JSON from Kafka value
    tweets = raw_stream \
        .select(
            from_json(
                col("value").cast("string"),
                RAW_TWEET_SCHEMA
            ).alias("tweet")
        ) \
        .select("tweet.*")
    
    # Apply transformations
    processed = tweets \
        .withColumn("tweet_id", col("id")) \
        .withColumn("original_text", col("text")) \
        .withColumn("cleaned_text", clean_text_udf(col("text"))) \
        .withColumn("sentiment", analyze_sentiment_udf(col("cleaned_text"))) \
        .withColumn("keywords", extract_keywords_udf(col("cleaned_text"))) \
        .withColumn("hashtags", lower(col("entities.hashtags").cast("string"))) \
        .withColumn("mentions", lower(col("entities.mentions").cast("string"))) \
        .withColumn("processed_at", current_timestamp())
    
    # Flatten sentiment struct for ElasticSearch
    final_output = processed.select(
        col("tweet_id"),
        col("original_text"),
        col("cleaned_text"),
        col("sentiment.label").alias("sentiment_label"),
        col("sentiment.score").alias("sentiment_score"),
        col("hashtags"),
        col("mentions"),
        col("keywords"),
        col("author_id"),
        col("created_at"),
        col("processed_at")
    )
    
    # Write to ElasticSearch
    query = final_output.writeStream \
        .format("org.elasticsearch.spark.sql") \
        .option("es.nodes", es_nodes) \
        .option("es.resource", es_index) \
        .option("es.nodes.wan.only", "true") \
        .option("checkpointLocation", "/tmp/checkpoint/es") \
        .outputMode("append") \
        .start()
    
    print("Streaming query started. Awaiting termination...")
    query.awaitTermination()


def main():
    """
    Main entry point for the Spark streaming application.
    """
    import os
    
    # Configuration
    KAFKA_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    INPUT_TOPIC = os.getenv('KAFKA_TOPIC', 'tweets_raw')
    ES_NODES = os.getenv('ELASTICSEARCH_NODES', 'elasticsearch:9200')
    ES_INDEX = os.getenv('ELASTICSEARCH_INDEX', 'brand_tweets')
    
    # Create Spark session
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        process_tweets(
            spark=spark,
            kafka_servers=KAFKA_SERVERS,
            input_topic=INPUT_TOPIC,
            es_nodes=ES_NODES,
            es_index=ES_INDEX
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        spark.stop()


if __name__ == '__main__':
    main()
