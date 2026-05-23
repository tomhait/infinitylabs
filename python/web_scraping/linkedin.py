import httpx
from bs4 import BeautifulSoup

def scrape_linkedin(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        with httpx.Client(http2=True, headers=headers) as client:
            response = client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            job_cards = soup.find_all("div", class_="base-search-card")

            job_list = []
            print(f"Found {len(job_cards)} jobs in the raw HTML. Parsing...")

            for card in job_cards:
                try:
                    title = card.find("h3", class_="base-search-card__title").text.strip()
                    company = card.find("h4", class_="base-search-card__subtitle").text.strip()
                    link = card.find("a", class_="base-card__full-link")["href"]

                    job_object = {
                        "Title": title,
                        "Company": company,
                        "Link": link.split("?")[0]
                    }
                    job_list.append(job_object)
                except Exception:
                    continue
            return job_list
    except httpx.HTTPStatusError as e:
        return {"error": f"Failed to retrieve page: {e}"}


if __name__ == "__main__":
    target_url = "https://www.linkedin.com/jobs/search/?keywords=Data Scientist&location=Israel"
    results = scrape_linkedin(target_url)

    for res in results:
        print(f"Job Title: {res['Title']}")
        print(f"Company: {res['Company']}")
        print(f"Offer link: {res['Link']}")