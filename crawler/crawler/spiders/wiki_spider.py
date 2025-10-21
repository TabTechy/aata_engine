import scrapy
from bs4 import BeautifulSoup
import hashlib
import re  # for whitespace normalization


class WikiSpider(scrapy.Spider):
    name = "wiki"
    start_urls = ["https://en.wikipedia.org/wiki/Artificial_intelligence"]

    custom_settings = {
        "CLOSESPIDER_PAGECOUNT": 1000,     # Target: 1000 pages
        "DOWNLOAD_DELAY": 0.7,             # Safe delay
        "CONCURRENT_REQUESTS": 8,          # Balanced speed
        "DEPTH_LIMIT": 3,                  # Prevent overly deep crawling
        "ROBOTSTXT_OBEY": True,
        "LOG_LEVEL": "INFO",
        "FEED_EXPORT_ENCODING": "utf-8"
    }

    def generate_id(self, url):
        """Generate a stable 12-character hash ID based on the URL."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def parse(self, response):
        soup = BeautifulSoup(response.text, "lxml")

        # ---------- Remove inline citations ----------
        for sup in soup.find_all("sup"):
            sup.replace_with(" ")  # replace with space instead of decompose

        # ---------- Remove References section ----------
        references_section = soup.find("span", {"id": "References"})
        if references_section:
            parent = references_section.find_parent("h2")
            if parent:
                for sibling in parent.find_next_siblings():
                    sibling.decompose()
                parent.decompose()

        # ---------- Extract title ----------
        title_tag = soup.find("h1", {"id": "firstHeading"})
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # ---------- Extract headings ----------
        headings = [h.get_text(strip=True) for h in soup.find_all(['h2', 'h3'])]

        # ---------- Extract cleaned main content ----------
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all('p')]
        content = " ".join(paragraphs)
        content = re.sub(r'\s+', ' ', content).strip()  # normalize spaces

        # ---------- Extract up to 15 unique internal wiki links ----------
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("/wiki/") and not any(x in href for x in [":", "#"]):
                full_url = response.urljoin(href)
                if full_url not in links:
                    links.append(full_url)
                    if len(links) <= 15:
                        yield response.follow(full_url, callback=self.parse)

        # ---------- Yield the structured item ----------
        yield {
            "id": self.generate_id(response.url),
            "content": content,
            "metadata": {
                "url": response.url,
                "title": title,
                "headings": headings,
                "links": links[:10]
            }
        }
