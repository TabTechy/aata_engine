import requests
from bs4 import BeautifulSoup
import json
import os
import time

# ---------- Config ----------
OUTPUT_FILE = os.path.join("..", "data", "data.json")
SEED_URL = "https://en.wikipedia.org/wiki/Artificial_intelligence"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MiniSearchBot/0.1)"}
MAX_PAGES = 5  # safe demo number
POLITE_DELAY = 1  # seconds

# ---------- Storage ----------
visited = set()
data = []

# ---------- Crawl + Scrape function ----------
def crawl_page(url):
    if url in visited or len(data) >= MAX_PAGES:
        return
    visited.add(url)
    print(f"Crawling: {url}")

    try:
        resp = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(resp.text, "html.parser")

        # --- Title ---
        title_tag = soup.find("title")
        title = title_tag.get_text().replace(" - Wikipedia", "") if title_tag else "No title"

        # --- Main content ---
        content_div = soup.find("div", {"id": "mw-content-text"})
        content = ""
        if content_div:
            paragraphs = content_div.find_all("p")
            content = " ".join(
                p.get_text(strip=True)
                for p in paragraphs
                if p.get_text(strip=True)
            )

        # --- Save page if content exists ---
        if content:
            data.append({
                "url": url,
                "title": title,
                "content": content[:5000]  # save first 5000 chars to keep JSON manageable
            })

        # --- Follow internal links (safe, limited) ---
        if len(data) < MAX_PAGES:
            links = content_div.find_all("a", href=True) if content_div else []
            for link in links:
                href = link["href"]
                if href.startswith("/wiki/") and not any(x in href for x in [":", "#"]):
                    next_url = "https://en.wikipedia.org" + href
                    if next_url not in visited and len(data) < MAX_PAGES:
                        time.sleep(POLITE_DELAY)
                        crawl_page(next_url)

    except Exception as e:
        print(f"Failed to crawl {url}: {e}")

# ---------- Main ----------
if __name__ == "__main__":
    crawl_page(SEED_URL)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Finished crawling {len(data)} pages. Data saved to {OUTPUT_FILE}")
