# agents/pdf_loader.py

from langchain.document_loaders import PyPDFLoader
from .base import BaseAgent, log

class PDFLoaderAgent(BaseAgent):
    def run(self, pdf_path, logs=None):
        log(f"PDFLoader: Loading and chunking PDF: {pdf_path}", logs)
        loader = PyPDFLoader(pdf_path)
        docs = loader.load_and_split()
        return [{"content": doc.page_content, "url": pdf_path, "title": "Uploaded PDF"} for doc in docs]
