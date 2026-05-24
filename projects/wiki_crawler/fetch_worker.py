import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
import datetime
from pymongo import MongoClient, ReturnDocument
from pathlib import Path

folder_path = Path("/app/storage/html_files")
folder_path.mkdir(parents=True, exist_ok=True)

client = MongoClient('mongodb://mongodb-core:27017/')
db = client['Wikipedia_DB']
collection = db['Html']
collection.create_index("name", unique=True)

timeout_config = aiohttp.ClientTimeout(total=15)

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def save_html(file_path, html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        await file.write(soup.prettify())

def update_db(webpage_name):
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    result = collection.find_one_and_update(
        {"_id": "shared_user_id"},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    document = {
        'id': result["sequence_value"],
        'name': webpage_name,
        'file_path': str(folder_path / f"{webpage_name}.html"),
        'timestamp': timestamp
    }
    insert_result = collection.update_one(
        {"name": webpage_name},
        {"$set": document},
        upsert=True
    )
    document.pop('_id', None)
    print(f"Successfully processed: {webpage_name} (ID: {insert_result.upserted_id})")
    return document

async def fetch_html(url, retries=3, initial_delay=2):
    webpage_name = url.split("/")[-1]
    if len(webpage_name) == 0:
        webpage_name = "root"

    delay = initial_delay

    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=timeout_config) as session:
                async with session.get(url) as response:
                    if response.status == 429:
                        if attempt < retries - 1:
                            await asyncio.sleep(delay * 2)
                            delay *= 2
                            continue
                        else:
                            return {"error": "Max retries reached. Continually rate limited (HTTP 429)."}
                    response.raise_for_status()
                    html_text = await response.text()
                    document = update_db(webpage_name)
                    await save_html(document['file_path'], html_text)
                    return document

        except aiohttp.ClientResponseError as e:
            if e.status in [404, 403, 400]:
                print(f"Permanent HTTP error {e.status} for {url}.")
                return {"error": f"Permanent error (Status {e.status}): {e.message}"}

            if attempt < retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
            else:
                return {"error": f"Max retries reached. Final HTTP error (Status {e.status}): {e.message}"}