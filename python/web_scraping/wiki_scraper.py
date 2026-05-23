import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_wiki_links(url, current_depth, max_depth, visited):
    if current_depth > max_depth or url in visited:
        return set()

    visited.add(url)

    print(f"Scraping {url} \n at depth {current_depth}")

    internal_links = set()
    try:
        with httpx.Client(http2=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.find(id="bodyContent")
            if content:
                for link in content.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/wiki/'):
                        full_url = urljoin("https://en.wikipedia.org", href)
                        internal_links.add(full_url)
                if current_depth < max_depth:
                    for link in list(internal_links):
                        scrape_wiki_links(link, current_depth + 1, max_depth, visited)
            return visited
    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to retrieve page: {e}"}

if __name__ == "__main__":
    start_page = "https://en.wikipedia.org/wiki/Document_Object_Model"
    max_crawl_depth = 1
    all_visited_links = scrape_wiki_links(start_page, 0, max_crawl_depth, set())
    print(f"\nTotal unique internal links found: {len(all_visited_links)}")
    for link in all_visited_links:
        print(link)