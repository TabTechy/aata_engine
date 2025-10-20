import scrapy
from bs4 import BeautifulSoup
import hashlib  # for generating unique IDs


class WikiSpider(scrapy.Spider):
    name = "wiki"
    start_urls = ["https://en.wikipedia.org/wiki/Artificial_intelligence"]

    # Allow up to 100 pages
    custom_settings = {
        "CLOSESPIDER_PAGECOUNT": 100,
        "DOWNLOAD_DELAY": 0.5,
        "ROBOTSTXT_OBEY": True
    }

    def generate_id(self, url):
        return hashlib.md5(url.encode()).hexdigest()[:12]  # short, readable ID

    def parse(self, response):
        soup = BeautifulSoup(response.text, "lxml")

        # ✅ Remove inline citations like [1], [2]
        for sup in soup.find_all("sup"):
            sup.decompose()

        # ✅ Remove entire references section
        references_section = soup.find("span", {"id": "References"})
        if references_section:
            parent = references_section.find_parent("h2")
            if parent:
                for sibling in parent.find_next_siblings():
                    sibling.decompose()
                parent.decompose()

        # ✅ Extract title
        title_tag = soup.find("h1", {"id": "firstHeading"})
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # ✅ Extract headings
        headings = [h.get_text(strip=True) for h in soup.find_all(['h2', 'h3'])]

        # ✅ Extract main content
        content = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))

        # ✅ Create combined_text for search indexing
        combined_text = f"{title} {' '.join(headings)} {content}".strip()

        # ✅ Extract top 10 internal Wikipedia links & follow them
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("/wiki/") and not any(x in href for x in [":", "#"]):
                full_url = response.urljoin(href)
                links.append(full_url)
                yield response.follow(full_url, callback=self.parse)

        # ✅ Yield in CLEAN format
        yield {
            "id": self.generate_id(response.url),
            "url": response.url,
            "title": title,
            "headings": headings,
            "content": content,
            "combined_text": combined_text,
            "links": links[:10]
        }
