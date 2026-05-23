import httpx
from bs4 import BeautifulSoup

def get_wikipedia_languages(url):
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    try:
        with httpx.Client(http2=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            lang_elements = soup.select('.interlanguage-link a, .interwiki-lang a')

            languages = []
            for link in lang_elements:
                lang_name = link.get_text(strip=True)
                if lang_name:
                    languages.append(lang_name)

            return languages

    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to retrieve page: {e}"}

url = "https://en.wikipedia.org/wiki/Document_Object_Model"
print(get_wikipedia_languages(url))