"""
Reset ElasticSearch Data - Deletes all tweets and recreates index.

WARNING: This will permanently delete all your tweet data!

Usage:
    python src/utils/reset_data.py
"""

from elasticsearch import Elasticsearch


def main():
    print("=" * 60)
    print("⚠️  RESET ELASTICSEARCH DATA")
    print("=" * 60)
    print()
    print("WARNING: This will DELETE all tweets in ElasticSearch!")
    print()
    
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != "DELETE":
        print("\n❌ Cancelled. No data was deleted.")
        return
    
    ES_HOST = "http://localhost:9200"
    INDEX_NAME = "brand_tweets"
    
    try:
        es = Elasticsearch([ES_HOST])
        es.info()
        print(f"\n✅ Connected to ElasticSearch")
    except Exception as e:
        print(f"\n❌ Failed to connect: {e}")
        return
    
    if es.indices.exists(index=INDEX_NAME):
        count = es.count(index=INDEX_NAME)["count"]
        print(f"\n🗑️  Deleting index '{INDEX_NAME}' with {count} tweets...")
        es.indices.delete(index=INDEX_NAME)
        print(f"✅ Index deleted!")
    else:
        print(f"\n⚠️  Index '{INDEX_NAME}' doesn't exist")
    
    print("\n" + "=" * 60)
    print("✅ Reset complete!")
    print("   Run start_pipeline.bat to reload fresh data")
    print("=" * 60)


if __name__ == "__main__":
    main()
