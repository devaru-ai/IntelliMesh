# agents/chunker.py

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from .base import BaseAgent, log

class ChunkerAgent(BaseAgent):
    def __init__(self, name, llm, embedding_model_name="sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__(name, llm)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

    def run(self, scraped_sources, logs=None):
        log("Chunker: Splitting documents into chunks...", logs)
        docs = []
        for source in scraped_sources:
            content = source.get("content", "")
            if not content.strip():
                continue
            doc = Document(
                page_content=content,
                metadata={"url": source.get("url", ""), "title": source.get("title", "")}
            )
            docs.append(doc)
        splits = self.text_splitter.split_documents(docs)
        log(f"Chunker: Created {len(splits)} chunks.", logs)
        vectorstore = Chroma.from_documents(splits, embedding=self.embeddings)
        log("Chunker: Vectorstore ready.", logs)
        return vectorstore
