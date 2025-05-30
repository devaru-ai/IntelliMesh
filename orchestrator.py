from agents.retriever import RetrieverAgent
from agents.scraper import ScraperAgent
from agents.evaluator import EvaluatorAgent
from agents.chunker import ChunkerAgent
from agents.synthesizer import SynthesizerAgent
from agents.planner import PlannerAgent
from agents.pdf_loader import PDFLoaderAgent

class Orchestrator:
    def __init__(self, retriever, scraper, evaluator, chunker, synthesizer, planner, pdf_loader):
        self.retriever = retriever
        self.scraper = scraper
        self.evaluator = evaluator
        self.chunker = chunker
        self.synthesizer = synthesizer
        self.planner = planner
        self.pdf_loader = pdf_loader

    def run(self, topic, pdf_path=None, logs=None):
        pdf_uploaded = pdf_path is not None
        flow_number, reason = self.planner.run(topic, pdf_uploaded)
        if logs is not None:
            logs.append(f"Planner chose flow {flow_number}: {reason}")

        if flow_number == 3 and pdf_uploaded:
            logs.append("Pipeline: Load PDF > Chunk > Synthesize")
            pdf_docs = self.pdf_loader.run(pdf_path, logs=logs)
            summary = self.synthesizer.run(topic, self.chunker.run(pdf_docs))
            return summary

        elif flow_number == 1:
            logs.append("Pipeline: Retrieve > Scrape > Synthesize")
            sources = self.retriever.run(topic, logs=logs)
            scraped = self.scraper.run(sources, self.retriever, topic, logs=logs)
            summary = self.synthesizer.run(topic, self.chunker.run(scraped))
            return summary

        elif flow_number == 2:
            logs.append("Pipeline: Retrieve > Scrape > Evaluate > Synthesize")
            sources = self.retriever.run(topic, logs=logs)
            scraped = self.scraper.run(sources, self.retriever, topic, logs=logs)
            curated = self.evaluator.run(scraped, query=topic, logs=logs)
            summary = self.synthesizer.run(topic, self.chunker.run(curated))
            return summary

        else:
            logs.append("Unknown pipeline flow. Defaulting to pipeline 2.")
            sources = self.retriever.run(topic, logs=logs)
            scraped = self.scraper.run(sources, self.retriever, topic, logs=logs)
            curated = self.evaluator.run(scraped, query=topic, logs=logs)
            summary = self.synthesizer.run(topic, self.chunker.run(curated))
            return summary
