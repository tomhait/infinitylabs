import os
import sys
import json
import socket
import asyncio
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from fetch_worker import fetch_html
from parse_worker import get_urls
from validate_worker import get_unvisited_urls


BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
GROUP_ID = os.getenv("GROUP_ID")
INPUT_TOPIC = os.getenv("INPUT_TOPIC")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC")
CONTAINER_ID = socket.gethostname()

if not GROUP_ID or not INPUT_TOPIC:
    print("Missing critical environment variables (GROUP_ID or INPUT_TOPIC). Exiting.")
    sys.exit(1)


async def process_payload(topic, data):
    if data.get('url'):
        webpage_name = data.get('url').split("/")[-1]
    else:
        webpage_name = data.get('document').get('name')

    if topic == "fetch-queue":
        print(f"[{CONTAINER_ID}] Fetching data for url: {webpage_name}")
        document = await fetch_html(data['url'])
        if 'error' in document:
            print(f"[{CONTAINER_ID}] Skipping task {webpage_name} because download failed: {document['error']}")
            return None
        data["document"] = document
        return data

    elif topic == "parse-queue":
        print(f"[{CONTAINER_ID}] Parsing raw text for task: {webpage_name}")
        links = get_urls(data['document']['file_path'])
        data['subpages'] = None
        if links:
            data['subpages'] = links
        return data

    elif topic == "validate-queue":
        print(f"[{CONTAINER_ID}] Validating task: {webpage_name}")
        unvisited_links = get_unvisited_urls(data['subpages'])
        if unvisited_links:
            fetch_tasks = []
            for i, url in enumerate(unvisited_links):
                new_fetch_task = {
                    "job_id": f"derived-{data.get('job_id', i)}",
                    "url": url
                }
                fetch_tasks.append(new_fetch_task)
            return fetch_tasks
        else:
            print(f"[{CONTAINER_ID}] Validation finished. No new links discovered. Ending lifecycle.")
            return None

async def main():
    consumer = AIOKafkaConsumer(
        INPUT_TOPIC,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        auto_offset_reset='earliest',
        enable_auto_commit=False,
        max_poll_interval_ms=900000
    )

    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS) if OUTPUT_TOPIC else None

    await consumer.start()
    if producer:
        await producer.start()
    print(f"Worker initialized | Container: {CONTAINER_ID} | Listening to: {INPUT_TOPIC} | Group: {GROUP_ID}")

    try:
        async for msg in consumer:
            payload = json.loads(msg.value.decode('utf-8'))

            updated_payload = await process_payload(msg.topic, payload)

            if producer and OUTPUT_TOPIC and updated_payload is not None:
                if isinstance(updated_payload, list):
                    for task in updated_payload:
                        key_bytes = str(task.get("job_id")).encode('utf-8')
                        val_bytes = json.dumps(task).encode('utf-8')
                        await producer.send_and_wait(OUTPUT_TOPIC, value=val_bytes, key=key_bytes)
                else:
                    val_bytes = json.dumps(updated_payload).encode('utf-8')
                    await producer.send_and_wait(OUTPUT_TOPIC, value=val_bytes, key=msg.key)

            await consumer.commit()

    except asyncio.CancelledError:
        print("Gracefully shutting down worker process...")
    finally:
        await consumer.stop()
        if producer:
            await producer.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Process interrupted by user.")