import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse

# -----------------------
# CONFIGURATION
# -----------------------
START_URL = "https://en.wikipedia.org/wiki/Artificial_intelligence"  # seed page
MAX_PAGES = 50  # number of pages to crawl
OUTPUT_FILE = "../data/data.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

# -----------------------
# HELPER FUNCTIONS
# -----------------------
def get_main_content(soup):
    """
    Extracts all paragraph text inside the main content div
    """
    content_div = soup.find("div", {"id": "mw-content-text"})
    if not content_div:
        return ""
    paragraphs = content_div.find_all("p")
    text = "\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
    return text

def is_valid_wiki_link(href):
    """
    Checks if the link is an internal Wikipedia link (skips special pages)
    """
    if href and href.startswith("/wiki/") and not any(prefix in href for prefix in [":", "#"]):
        return True
    return False

# -----------------------
# MAIN CRAWLER
# -----------------------
to_crawl = [START_URL]
crawled = set()
data = []

while to_crawl and len(crawled) < MAX_PAGES:
    url = to_crawl.pop(0)
    if url in crawled:
        continue

    try:
        print(f"Crawling: {url}")
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        # Get title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "No title"

        # Get main content
        content = get_main_content(soup)

        # Save result
        data.append({
            "url": url,
            "title": title,
            "content": content
        })

        crawled.add(url)

        # Find all internal Wikipedia links and add to queue
        for link in soup.find_all("a", href=True):
            href = link['href']
            if is_valid_wiki_link(href):
                full_url = urljoin("https://en.wikipedia.org", href)
                if full_url not in crawled and full_url not in to_crawl:
                    to_crawl.append(full_url)

        # Sleep 1 second to avoid overloading server
        time.sleep(1)

    except Exception as e:
        print(f"Failed to crawl {url}: {e}")
        continue

print(f"Finished crawling {len(crawled)} pages. Data saved to {OUTPUT_FILE}")

# -----------------------
# SAVE TO JSON
# -----------------------
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)
