import requests
from bs4 import BeautifulSoup
import json
import time

# Step 1: Pick a page to crawl (Wikipedia is safe)
url = "https://en.wikipedia.org/wiki/Artificial_intelligence"

# Step 2: Fetch the page
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
html = response.text
print(html[:1000])  # Print first 1000 characters of HTML

# Step 3: Parse the HTML
soup = BeautifulSoup(html, "html.parser")

# Extract the title (Wikipedia main heading)
title_tag = soup.find("h1", {"id": "firstHeading"})
title = title_tag.get_text(strip=True) if title_tag else "No title"
print("Raw title tag:", soup.title)

# Extract the first non-empty paragraph inside content
content_div = soup.find("div", {"id": "mw-content-text"})
paragraphs = content_div.find_all("p") if content_div else []

first_para = ""
for p in paragraphs:
    text = p.get_text(strip=True)
    if text:
        first_para = text
        break

# Step 4: Store in a Python dict
data = {
    "url": url,
    "title": title,
    "content": first_para
}

# Step 5: Save to a JSON file
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Crawled and saved:", title)
