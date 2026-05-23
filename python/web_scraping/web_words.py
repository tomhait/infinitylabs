import httpx
import re
from bs4 import BeautifulSoup

def get_sorted_webpage_words(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    try:
        with httpx.Client(http2=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            for element in soup(["script", "style"]):
                element.extract()
            text = soup.get_text(separator=' ', strip=True)
            words = re.findall(r'\b[\w\'-]+\b', text.lower())
            unique_words = sorted(list(set(words)))
            sorted_words = sorted(unique_words, key=lambda x: len(x), reverse=True)
            return sorted_words
    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to retrieve page: {e}"}


url = "https://en.wikipedia.org/wiki/Document_Object_Model"
print(get_sorted_webpage_words(url))