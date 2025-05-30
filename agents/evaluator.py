# agents/evaluator.py

from .base import BaseAgent, log

class EvaluatorAgent(BaseAgent):
    def run(self, sources, query=None, min_length=200, top_k=5, logs=None):
        filtered = []
        for src in sources:
            content = src.get("content", "") or src.get("snippet", "")
            if len(content.strip()) >= min_length:
                filtered.append(src)
            else:
                log(f"Evaluator: Skipping short content from {src.get('url', '')}", logs)

        # Deduplicate by URL
        seen_urls = set()
        deduped = []
        for src in filtered:
            url = src.get("url", "")
            if url and url not in seen_urls:
                deduped.append(src)
                seen_urls.add(url)
            elif not url:
                deduped.append(src)  # If no URL, keep (rare)

        # Rank by keyword overlap with query
        if query:
            query_words = set(query.lower().split())
            def relevance(src):
                content = (src.get("content", "") or src.get("snippet", "")).lower()
                return sum(word in content for word in query_words)
            deduped.sort(key=relevance, reverse=True)

        # Prefer trusted domains
        trusted_domains = [".edu", ".gov", ".ac.uk", "mit.edu", "nature.com", "sciencedirect.com"]
        trusted = []
        others = []
        for src in deduped:
            url = src.get("url", "")
            if any(domain in url for domain in trusted_domains):
                trusted.append(src)
            else:
                others.append(src)

        # Select top_k, prioritizing trusted, but fill with others if needed
        final = []
        for src in trusted:
            if len(final) < top_k:
                final.append(src)
        for src in others:
            if len(final) < top_k:
                final.append(src)

        log(f"Evaluator: Selected {len(final)} sources (trusted: {len(trusted)}) out of {len(sources)} input sources.", logs)
        return final
