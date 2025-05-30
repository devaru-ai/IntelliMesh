# agents/synthesizer.py

import re
from .base import BaseAgent, log

class SynthesizerAgent(BaseAgent):
    def run(self, query, vectorstore):
        retriever = vectorstore.as_retriever()
        relevant_docs = retriever.get_relevant_documents(query)
        context = ""
        cited = {}
        for doc in relevant_docs:
            meta = doc.metadata
            url = meta.get('url', '')
            title = meta.get('title', '') or url
            if url and url not in cited:
                cited[url] = title
            context += f"{doc.page_content}\n\n"

        ai_keywords = [
            "ai", "artificial intelligence", "machine learning", "generative",
            "research", "science", "scientific"
        ]
        if any(word in query.lower() for word in ai_keywords):
            prompt = (
                f"Using only the context below, write a nuanced and engaging summary answering the question. "
                f"Highlight how generative AI is changing scientific research, giving concrete examples where possible. "
                f"Discuss both the transformative benefits and the most pressing challenges, making connections between them. "
                f"Conclude with a sentence on the importance of responsible adoption and human oversight. "
                f"Write in a clear, professional, but lively style as if for a science magazine or a research newsletter. "
                f"At the end, list each unique source in markdown link format as a clean, deduplicated list.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {query}\n"
                f"Answer:"
            )
        else:
            prompt = (
                f"Using only the context below, write a clear, engaging, and accurate summary answering the question. "
                f"Focus on the main facts, insights, and relevant details. "
                f"At the end, list each unique source in markdown link format as a clean, deduplicated list.\n\n"
                f"Context:\n{context}\n\n"
                f"Question: {query}\n"
                f"Answer:"
            )

        answer = self.llm(prompt) if self.llm else prompt

        # Only display the part after "Answer:"
        if "Answer:" in answer:
            answer = answer.split("Answer:", 1)[1].strip()

        # Clean up duplicate sections if needed
        answer = re.sub(r'\n?Note:.*(?:\n|$)', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'(\nSummary:.*?)(\nSummary:)', r'\2', answer, flags=re.IGNORECASE | re.DOTALL)
        answer = re.sub(r'(\nSources:.*?)(\nSources:)', r'\2', answer, flags=re.IGNORECASE | re.DOTALL)
        answer = re.sub(r'\n{3,}', '\n\n', answer)

        closing = (
            "\n\nResponsible adoption of generative AI-guided by transparency, ethical standards, and human oversight-"
            "will be essential to maximize its benefits and maintain trust in scientific research."
        )
        if any(word in query.lower() for word in ai_keywords):
            if closing.strip() not in answer:
                answer += closing

        if cited and "sources:" not in answer.lower():
            answer += "\n\nSources:\n"
            for url, title in cited.items():
                answer += f"- [{title}]({url})\n"

        return answer
