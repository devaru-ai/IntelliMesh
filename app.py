import gradio as gr
from orchestrator import orchestrator  # The instance, not the class
from utils import style_logs, style_answer
import time

def research_pipeline(query, pdf=None):
    logs = []
    pdf_path = pdf.name if pdf else None
    start_time = time.time()
    try:
        answer = orchestrator.run(query, pdf_path=pdf_path, logs=logs)
    except Exception as e:
        answer = "An error occurred during processing."
        logs.append(f"Error: {e}")
    elapsed = time.time() - start_time
    logs.append(f"✅ **Completed in {elapsed:.2f} seconds.**")
    return style_answer(answer), style_logs('\n'.join(logs))

custom_theme = gr.themes.Default(
    primary_hue="emerald",
    secondary_hue="sky",
    neutral_hue="gray",
    text_size="lg"
).set(
    block_background_fill="#f9f9f9",
    block_border_color="#e0e0e0"
)

with gr.Blocks(theme=custom_theme) as demo:
    gr.Markdown("# 🤖 IntelliMesh: Modular Multi-Agent Research System")
    with gr.Row():
        query = gr.Textbox(label="🔍 Ask a research question", scale=3)
        pdf = gr.File(label="📄 Upload PDF (optional)", file_types=[".pdf"], scale=2)
    btn = gr.Button("🚀  Run Research", variant="primary")
    answer = gr.Markdown(label="📑 AI-Generated Summary")
    logbox = gr.Markdown(label="🧾 Logs")
    with gr.Tabs():
        with gr.Tab("📑 Summary"):
            answer = gr.Markdown()
        with gr.Tab("📜 Logs"):
            logbox = gr.Markdown()
    def show_processing():
        return gr.update(interactive=False), "", "⏳ Running agents..."
    btn.click(
        show_processing,
        inputs=[],
        outputs=[btn, answer, logbox],
        queue=False
    ).then(
        research_pipeline,
        inputs=[query, pdf],
        outputs=[answer, logbox]
    ).then(
        lambda: gr.update(interactive=True),
        None,
        btn
    )
demo.launch()
