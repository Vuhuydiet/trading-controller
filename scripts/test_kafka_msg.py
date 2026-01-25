# scripts/test_kafka_msg.py
import json
from kafka import KafkaProducer
from datetime import datetime

# Cấu hình
KAFKA_SERVER = 'localhost:9092'
TOPIC = 'news.articles'

def send_test_news():
    try:
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_SERVER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # Tạo tin tức giả
        dummy_news = {
            "url": "btc-news-test-01",
            "title": "Elon Musk tuyên bố mua thêm 1 tỷ USD Bitcoin",
            "content": "Giá BTC dự kiến sẽ tăng mạnh sau tin này...",
            "source": "Breaking News",
            "published_at": datetime.now().isoformat()
        }

        print(f"Sending mock news to topic '{TOPIC}'...")
        producer.send(TOPIC, dummy_news)
        producer.flush()
        print("Message sent successfully!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_test_news()