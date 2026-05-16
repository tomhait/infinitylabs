import asyncio
import aiohttp
import json
from functools import wraps
from datetime import datetime


def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

class Products:
    def __init__(self, base_url, limit=10):
        self.base_url = base_url
        self.limit = limit
        self.output_file = './processed_products.json'
        self.queue = asyncio.Queue(maxsize=15)
        self.file_lock = asyncio.Lock()

    async def producer(self, session, total_items=200):
        """
        The Producer: Fetches pages from the base url
        and adds them to the queue.
        """
        for offset in range(0, total_items, self.limit):
            params = {'limit': self.limit, 'skip': offset}
            async with session.get(self.base_url, params=params) as resp:
                data = await resp.json()
                batch = data.get('products', [])
                print(f"Producer - Fetched batch: {offset}")
                await self.queue.put(batch)
        await self.queue.put(None)

    async def consumer(self, session):
        """The Consumer: Handles image downloads and JSON metadata."""
        while True:
            batch = await self.queue.get()
            if batch is None:
                self.queue.task_done()
                break

            for item in batch:
                img_url = item.get('thumbnail')
                if img_url:
                    async with session.get(img_url) as img_resp:
                        _ = await img_resp.read()
                async with self.file_lock:
                    with open(self.output_file, mode='a') as f:
                        f.write(json.dumps(item) + "\n")

            print(f"Consumer - Processed {len(batch)} items")
            self.queue.task_done()

    async def run(self):
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                self.producer(session),
                self.consumer(session)
            )


@func_timer
def run():
    pipeline = Products("https://dummyjson.com/products")
    asyncio.run(pipeline.run())


if __name__ == "__main__":
    run()

