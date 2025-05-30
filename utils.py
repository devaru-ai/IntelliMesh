import re
from datetime import datetime

def style_logs(logs_text):
    styled = "<details><summary>📜 Click to expand full pipeline logs</summary>\n\n"
    styled += "### 🔧 Pipeline Execution Log\n\n"
    lines = logs_text.splitlines()
    new_lines = []
    url_counter = 1
    for line in lines:
        ts = datetime.now().strftime("[%H:%M:%S]")
        if "Scraping http" in line:
            line = re.sub(r"(Scraping )", f"Scraping URL {url_counter}/5 - ", line)
            url_counter += 1
        elif any(agent in line for agent in ["Retriever", "Scraper", "Evaluator", "Chunker", "Synthesizer", "PDFLoader"]):
            line = f"{ts} > **{line}**"
        new_lines.append(line)
    logs_text = '\n'.join(new_lines)
    logs_text = re.sub(r"(Planner chose flow \d+: [^\n]+)", r"> 🔁 **\1**", logs_text)
    logs_text = re.sub(r"(Pipeline: [^\n]+)", r"**\1**", logs_text)
    for label in ["Retriever", "Scraper", "Evaluator", "Chunker", "Synthesizer", "PDFLoader"]:
        logs_text = re.sub(rf"\b({label}):", rf"**\1:**", logs_text)
    logs_text = re.sub(r"(Fetching|Scraping|Retrieving|Evaluating|Chunking|Synthesizing)", r"🔄 \1", logs_text, flags=re.IGNORECASE)
    logs_text = re.sub(r"(Selected|Success|Succeeded|Found)", r"✅ **\1**", logs_text, flags=re.IGNORECASE)
    logs_text = re.sub(r"(Final scraped results: \d+)", r"📦 **\1**", logs_text)
    logs_text = re.sub(r"(Error|Exception)", r"❌ **\1**", logs_text, flags=re.IGNORECASE)
    logs_text = logs_text.replace('\n', '  \n')
    styled += logs_text + "\n</details>"
    return styled

def style_answer(answer_text):
    closing = "Responsible adoption of generative AI-guided by transparency, ethical standards, and human oversight-will be essential to maximize its benefits and maintain trust in scientific research."
    if closing in answer_text:
        answer_text = answer_text.replace(closing, f"**{closing}**")
    answer_text = re.sub(r"(Sources:)", r"\n\n### 📚 \1", answer_text)
    answer_text = answer_text.replace(". [", ".  \n[")
    return answer_text
