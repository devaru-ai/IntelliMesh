# agents/scraper.py

import requests
from bs4 import BeautifulSoup
from .base import BaseAgent, log

class ScraperAgent(BaseAgent):
    def run(self, sources, retriever, query, desired_count=5, max_attempts=3, logs=None):
        scraped_results = []
        attempted_urls = set()
        attempts = 0

        while len(scraped_results) < desired_count and attempts < max_attempts:
            log(f"Scraper: Attempt {attempts+1}, {len(scraped_results)} results so far", logs)
            for source in sources:
                url = source['url']
                if url in attempted_urls:
                    continue
                attempted_urls.add(url)
                log(f"Scraper: Scraping {url}", logs)
                try:
                    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                    soup = BeautifulSoup(resp.text, "html.parser")
                    content = soup.get_text(separator=" ", strip=True)
                    log(f"Scraper: Content length {len(content)}", logs)
                    if ("Access Denied" in content or "Enable JavaScript" in content or "Just a moment..." in content):
                        log(f"Scraper: Blocked or JS required for {url}", logs)
                        continue
                    if len(content) < 100:
                        log(f"Scraper: Content too short for {url}", logs)
                        continue
                    scraped_results.append({
                        "url": url,
                        "title": source.get("title", ""),
                        "content": content
                    })
                except Exception as e:
                    log(f"Scraper: Exception scraping {url}: {e}", logs)
            if len(scraped_results) < desired_count:
                extra_needed = desired_count - len(scraped_results)
                log(f"Scraper: Fetching {extra_needed} more URLs from retriever...", logs)
                sources = retriever.run(query, top_k=extra_needed * (attempts + 2))
            attempts += 1

        log(f"Scraper: Final scraped results: {len(scraped_results)}", logs)
        return scraped_results
