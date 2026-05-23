import os
import json
import time
import pymongo
from confluent_kafka import Producer

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

client = pymongo.MongoClient('mongodb://mongodb-core:27017/')
db = client['Wikipedia_DB']
collection = db['Html']

def init_queue():
    print("Manager initializing... Waiting for Kafka broker to be ready.")
    time.sleep(5)

    p = Producer({'bootstrap.servers': BOOTSTRAP_SERVERS})
    urls_to_scrape = [
        {"job_id": "job-001", "url": "https://en.wikipedia.org/", "document": None}
    ]
    latest_docs_cursor = collection.find().sort([('_id', -1)]).limit(20)
    latest_docs = list(latest_docs_cursor)
    is_parse = False
    if latest_docs:
        urls_to_scrape = []
        print(f"Download restarted. Found {len(latest_docs)} historical webpage records.")
        print("Injecting seed payloads into parse queue...")
        is_parse = True
        for i, doc in enumerate(latest_docs):
            doc.pop('_id', None)
            urls_to_scrape.append({
                "job_id": f"restart-{doc.get('id', i)}",
                "document": doc,
                "url": None
            })
    else:
        print("Beginning downloading Wikipedia Htmls")
        print("Injecting seed payload into fetch queue...")

    for item in urls_to_scrape:
        initial_payload = {
            "job_id": item["job_id"],
            "url": item["url"],
            "document": item["document"],
            "created_at": time.time()
        }

        p.produce(
            topic='fetch-queue' if not is_parse else 'parse-queue',
            key=str(initial_payload["job_id"]),
            value=json.dumps(initial_payload).encode('utf-8')
        )

        p.poll(0)

    p.flush()
    print("All seed payloads injected. Pipeline is now running automatically.")

if __name__ == "__main__":
    init_queue()