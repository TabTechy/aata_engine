import requests
from bs4 import BeautifulSoup
import json
import time
import os

# ---------- Headers for polite crawling ----------
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36"
}

# ---------- Function to crawl a single page ----------
def crawl_page(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract the title (Wikipedia main heading)
    title_tag = soup.find("h1", {"id": "firstHeading"})
    title = title_tag.get_text(strip=True) if title_tag else "No title"
    
    # Extract first non-empty paragraph inside content
    content_div = soup.find("div", {"id": "mw-content-text"})
    paragraphs = content_div.find_all("p") if content_div else []
    
    first_para = ""
    for p in paragraphs:
        text = p.get_text(strip=True)
        if text:
            first_para = text
            break
    
    return {
        "url": url,
        "title": title,
        "content": first_para
    }

# ---------- Function to get internal Wikipedia links ----------
def get_links(url):
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    
    content_div = soup.find("div", {"id": "mw-content-text"})
    links = []
    
    if content_div:
        for a in content_div.find_all("a", href=True):
            href = a['href']
            # Only internal Wikipedia links, skip files/special pages
            if href.startswith("/wiki/") and not any(x in href for x in [":", "#"]):
                full_url = "https://en.wikipedia.org" + href
                links.append(full_url)
    return links

# ---------- Main crawling logic ----------
start_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
to_crawl = [start_url]
crawled = []
visited = set()
max_pages = 5  # safe number for demo
output_file = os.path.join("..", "data", "data.json")  # save in data folder

while to_crawl and len(crawled) < max_pages:
    url = to_crawl.pop(0)
    if url in visited:
        continue
    print("Crawling:", url)
    
    data = crawl_page(url)
    crawled.append(data)
    visited.add(url)
    
    # Get more links to crawl, but don’t exceed max_pages
    new_links = get_links(url)
    for link in new_links:
        if link not in visited and len(crawled) + len(to_crawl) < max_pages:
            to_crawl.append(link)
    
    time.sleep(1)  # polite delay

# ---------- Save results ----------
os.makedirs(os.path.dirname(output_file), exist_ok=True)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(crawled, f, ensure_ascii=False, indent=4)

print(f"Finished crawling {len(crawled)} pages. Data saved to {output_file}")
