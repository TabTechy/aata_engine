import scrapy
from bs4 import BeautifulSoup
import hashlib  # for generating unique IDs


class WikiSpider(scrapy.Spider):
    name = "wiki"
    start_urls = ["https://en.wikipedia.org/wiki/Artificial_intelligence"]

    custom_settings = {
        "CLOSESPIDER_PAGECOUNT": 100,
        "DOWNLOAD_DELAY": 0.5,
        "ROBOTSTXT_OBEY": True
    }

    def generate_id(self, url):
        """Generate a stable 12-char hash ID based on URL."""
        return hashlib.md5(url.encode()).hexdigest()[:12]

    def parse(self, response):
        soup = BeautifulSoup(response.text, "lxml")

        # ✅ Remove inline citations like [1], [2]
        for sup in soup.find_all("sup"):
            sup.decompose()

        # ✅ Remove entire References section (and content below it)
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

        # ✅ Extract headings (H2, H3)
        headings = [h.get_text(strip=True) for h in soup.find_all(['h2', 'h3'])]

        # ✅ Extract cleaned main content
        content = ' '.join(p.get_text(strip=True) for p in soup.find_all('p'))

        # ✅ Extract up to 10 internal Wikipedia links (AND continue crawling)
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("/wiki/") and not any(x in href for x in [":", "#"]):
                full_url = response.urljoin(href)
                links.append(full_url)
                yield response.follow(full_url, callback=self.parse)

        # ✅ Yield in your final dataset format
        yield {
            "id": self.generate_id(response.url),
            "content": content,  # ✅ clean text for indexing
            "metadata": {
                "url": response.url,
                "title": title,
                "headings": headings,
                "links": links[:10]
            }
        }
