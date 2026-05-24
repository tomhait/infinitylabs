from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_urls(file_path):
    internal_links = set()
    with open(file_path, 'r') as fp:
        soup = BeautifulSoup(fp, 'html.parser')
        content = soup.find(id="bodyContent")
        if content:
            for link in content.find_all('a', href=True):
                href = link['href']
                if href.startswith('/wiki/') and not ':' in href:
                    full_url = urljoin("https://en.wikipedia.org", href)
                    internal_links.add(full_url)
                elif href.startswith('https://en.wikipedia.org/wiki/'):
                    internal_links.add(href)
    if internal_links:
        return list(internal_links)
    return None

