import time
import re
from collections import Counter

# --- LLM-as-a-Judge Prompts (Chain-of-Thought + rubric) ---
RELEVANCE_PROMPT = """
You are an expert evaluator. Given the user query and the system answer, first explain step by step how relevant the answer is to the query, then rate the relevance on a scale from 1 to 5, where:
1 = Completely irrelevant
2 = Slightly relevant
3 = Moderately relevant
4 = Mostly relevant
5 = Highly relevant

Query: {query}
Answer: {answer}

First, explain your reasoning. Then, on a new line, respond with only the number (1 to 5).
"""

FAITHFULNESS_PROMPT = """
You are an expert evaluator. Given the system answer and the supporting context, first explain step by step how faithful the answer is to the context. A faithful answer only contains information present in the context, and does not hallucinate or contradict the context. Then, rate the faithfulness on a scale from 1 to 5, where:
1 = Completely unfaithful (hallucinated, contradicts context)
2 = Slightly faithful
3 = Moderately faithful
4 = Mostly faithful
5 = Fully faithful (all info is in the context)

Context: {context}
Answer: {answer}

First, explain your reasoning. Then, on a new line, respond with only the number (1 to 5).
"""

# --- LLM-as-a-Judge Functions ---
def llm_judge_relevance(llm, query, answer):
    prompt = RELEVANCE_PROMPT.format(query=query, answer=answer)
    result = llm(prompt)
    matches = re.findall(r"\b[1-5]\b", result)
    return int(matches[-1]) if matches else 1

def llm_judge_faithfulness(llm, context, answer):
    prompt = FAITHFULNESS_PROMPT.format(context=context, answer=answer)
    result = llm(prompt)
    matches = re.findall(r"\b[1-5]\b", result)
    return int(matches[-1]) if matches else 1

# --- Evaluation for a single pipeline ---
def evaluate_pipeline(queries, orchestrator, llm, is_baseline=False, agent_usage=None):
    relevance_results = []
    faithfulness_results = []
    latencies = []
    successful_runs = 0
    total_runs = 0

    for query in queries:
        logs = []
        start = time.time()
        try:
            if is_baseline:
                # Baseline: Retriever only, no scraping/evaluation
                sources = orchestrator.retriever.run(query, logs=logs)
                if agent_usage is not None:
                    agent_usage['Retriever'] += 1
                pseudo_scraped = []
                for src in sources:
                    content = src.get("snippet", "") or src.get("title", "")
                    if content.strip():
                        pseudo_scraped.append({
                            "url": src.get("url", ""),
                            "title": src.get("title", ""),
                            "content": content
                        })
                if not pseudo_scraped:
                    answer = "No relevant information could be found for this query."
                    context = ""
                else:
                    vectorstore = orchestrator.chunker.run(pseudo_scraped, logs=logs)
                    if agent_usage is not None:
                        agent_usage['Chunker'] += 1
                    if vectorstore is None:
                        answer = "No relevant information could be found for this query."
                        context = ""
                    else:
                        answer = orchestrator.synthesizer.run(query, vectorstore)
                        if agent_usage is not None:
                            agent_usage['Synthesizer'] += 1
                        context = " ".join([doc["content"] for doc in pseudo_scraped[:3]])
            else:
                # Full pipeline (uses orchestrator)
                answer = orchestrator.run(query, logs=logs)
                # Count agent usage from logs (simple heuristic)
                if agent_usage is not None:
                    for agent in ['Retriever', 'Scraper', 'Evaluator', 'Chunker', 'Synthesizer']:
                        if any(agent in log for log in logs):
                            agent_usage[agent] += 1
                context = "\n".join(logs)[-2000:]
            end = time.time()
            latency = end - start
            latencies.append(latency)
            successful_runs += 1
        except Exception as e:
            print(f"Error: {e}")
            answer = ""
            context = ""
            end = time.time()
            latency = end - start
            latencies.append(latency)
        total_runs += 1

        # Judge relevance (CoT)
        relevance_score = llm_judge_relevance(llm, query, answer)
        relevance_results.append(relevance_score)

        # Judge faithfulness (CoT)
        faithfulness_score = llm_judge_faithfulness(llm, context, answer)
        faithfulness_results.append(faithfulness_score)

    # Normalize to [0, 1] for reporting
    relevance_norm = sum(relevance_results) / (5 * len(relevance_results)) if relevance_results else 0
    faithfulness_norm = sum(faithfulness_results) / (5 * len(faithfulness_results)) if faithfulness_results else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    return {
        "relevance": relevance_norm,
        "faithfulness": faithfulness_norm,
        "avg_latency": avg_latency,
        "throughput": len(queries) / sum(latencies) * 60 if latencies and sum(latencies) > 0 else 0,
        "uptime": successful_runs / total_runs if total_runs else 0,
        "error_rate": 1 - (successful_runs / total_runs) if total_runs else 1,
        "agent_usage": dict(agent_usage) if agent_usage is not None else None,
        "total_runs": total_runs
    }

# --- Benchmarking: Compare pipeline vs. baseline ---
def benchmark(queries, orchestrator, llm):
    agent_usage_pipeline = Counter({agent: 0 for agent in ['Retriever', 'Scraper', 'Evaluator', 'Chunker', 'Synthesizer']})
    agent_usage_baseline = Counter({agent: 0 for agent in ['Retriever', 'Scraper', 'Evaluator', 'Chunker', 'Synthesizer']})

    print("Evaluating full pipeline...")
    pipeline_scores = evaluate_pipeline(queries, orchestrator, llm, is_baseline=False, agent_usage=agent_usage_pipeline)
    print("Evaluating baseline (retriever only)...")
    baseline_scores = evaluate_pipeline(queries, orchestrator, llm, is_baseline=True, agent_usage=agent_usage_baseline)
    print("\nResults (normalized to 1.0):")
    print(f"{'System':<15} {'Relevance':<10} {'Faithfulness':<13} {'Latency (s)':<12} {'Throughput':<12} {'Uptime':<8} {'ErrorRate':<10}")
    print(f"{'Pipeline':<15} {pipeline_scores['relevance']:<10.2f} {pipeline_scores['faithfulness']:<13.2f} {pipeline_scores['avg_latency']:<12.2f} {pipeline_scores['throughput']:<12.2f} {pipeline_scores['uptime']*100:<8.1f}% {pipeline_scores['error_rate']*100:<10.1f}%")
    print(f"{'Baseline':<15} {baseline_scores['relevance']:<10.2f} {baseline_scores['faithfulness']:<13.2f} {baseline_scores['avg_latency']:<12.2f} {baseline_scores['throughput']:<12.2f} {baseline_scores['uptime']*100:<8.1f}% {baseline_scores['error_rate']*100:<10.1f}%")

    # Agent Utilization
    print("\nAgent Utilization (as % of runs):")
    for agent in agent_usage_pipeline:
        util = pipeline_scores['agent_usage'][agent] / pipeline_scores['total_runs'] * 100 if pipeline_scores['total_runs'] else 0
        print(f"Pipeline {agent}: {util:.1f}%")
    for agent in agent_usage_baseline:
        util = baseline_scores['agent_usage'][agent] / baseline_scores['total_runs'] * 100 if baseline_scores['total_runs'] else 0
        print(f"Baseline {agent}: {util:.1f}%")

    return {
        "pipeline": pipeline_scores,
        "baseline": baseline_scores
    }
