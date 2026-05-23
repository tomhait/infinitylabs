import os
import sys
import json
import socket
import asyncio
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

import pipeline_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("kafka_runner")

BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
GROUP_ID = os.getenv("GROUP_ID")
INPUT_TOPIC = os.getenv("INPUT_TOPIC")
OUTPUT_TOPIC = os.getenv("OUTPUT_TOPIC")
CONTAINER_ID = socket.gethostname()

if not all([GROUP_ID, INPUT_TOPIC]):
    logger.critical("Missing core deployment variables (GROUP_ID, INPUT_TOPIC).")
    sys.exit(1)


class StreamProcessor:
    def __init__(self):
        self.consumer = None
        self.producer = None
        self._handlers = {
            "fetch-queue": pipeline_worker.run_fetch_stage,
            "parse-queue": pipeline_worker.run_parse_stage,
            "validate-queue": pipeline_worker.run_validation_stage,
        }

    async def setup(self):
        self.consumer = AIOKafkaConsumer(
            INPUT_TOPIC,
            bootstrap_servers=BOOTSTRAP_SERVERS,
            group_id=GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            max_poll_interval_ms=900000,
        )
        await self.consumer.start()

        if OUTPUT_TOPIC:
            self.producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
            await self.producer.start()

        logger.info(f"Host: {CONTAINER_ID} | Topic: {INPUT_TOPIC} | Group: {GROUP_ID}")

    async def _dispatch_outbound(self, data, fallback_key):
        if not self.producer or not OUTPUT_TOPIC:
            return

        if isinstance(data, list):
            for item in data:
                key = str(item.get("job_id", "")).encode("utf-8")
                val = json.dumps(item).encode("utf-8")
                await self.producer.send_and_wait(OUTPUT_TOPIC, value=val, key=key)
        else:
            val = json.dumps(data).encode("utf-8")
            await self.producer.send_and_wait(OUTPUT_TOPIC, value=val, key=fallback_key)

    async def start_loop(self):
        try:
            async for msg in self.consumer:
                payload = json.loads(msg.value.decode("utf-8"))
                handler = self._handlers.get(msg.topic)

                if not handler:
                    logger.error(f"Dropping packet: No registered handler for {msg.topic}")
                    await self.consumer.commit()
                    continue

                result = await handler(payload)
                if result is not None:
                    await self._dispatch_outbound(result, msg.key)

                await self.consumer.commit()

        except asyncio.CancelledError:
            logger.info("Termination signal caught. Stopping components...")
        finally:
            if self.consumer:
                await self.consumer.stop()
            if self.producer:
                await self.producer.stop()


if __name__ == "__main__":
    processor = StreamProcessor()
    try:
        asyncio.run(processor.setup())
        asyncio.run(processor.start_loop())
    except KeyboardInterrupt:
        pass