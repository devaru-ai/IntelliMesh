# agents/retriever.py

import os
from langchain_community.utilities import GoogleSerperAPIWrapper
from .base import BaseAgent, log

class RetrieverAgent(BaseAgent):
    def run(self, query, top_k=5, logs=None):
        log(f"Retriever: Searching for '{query}'", logs)
        serper = GoogleSerperAPIWrapper(serper_api_key=os.environ["SERPER_API_KEY"])
        results = serper.results(query)
        urls = []
        if 'organic' in results:
            for item in results['organic'][:top_k]:
                if 'link' in item:
                    urls.append({
                        "url": item['link'],
                        "title": item.get('title', ''),
                        "snippet": item.get('snippet', '')
                    })
        log(f"Retriever: Found {len(urls)} URLs", logs)
        return urls
