"""The Unofficial Guide — Gradio query interface.

Run: python app.py   then open http://localhost:7860

Input:  a plain-language question about student life at Colby College.
Output: a grounded answer with inline [n] citations, the list of source
documents the answer drew from, and the raw retrieved chunks with their
cosine distances (so you can see what the answer is based on).
"""

import gradio as gr

from query import ask

EXAMPLES = [
    "What is Doghead and when does it happen?",
    "Can freshmen choose their dorm at Colby?",
    "Do Colby dorms have air conditioning?",
    "Which CS professor has the most organized lectures?",
    "How many on-campus Jan Plans are students expected to complete?",
]


def handle_query(question, use_hybrid):
    question = (question or "").strip()
    if not question:
        return "Please type a question first.", "", ""
    result = ask(question, hybrid=use_hybrid)
    sources = "\n".join(f"• {s}" for s in result["sources"]) or "(no sources — not covered by the documents)"
    chunks = "\n\n".join(
        f"[{i}] {'found by ' + h['found_by'] if use_hybrid else 'distance=' + str(h['distance'])}"
        f" — {h['source_doc']}\n{h['text']}"
        for i, h in enumerate(result["hits"], 1)
    )
    return result["answer"], sources, chunks


with gr.Blocks(title="The Unofficial Guide — Colby College") as demo:
    gr.Markdown(
        "# The Unofficial Guide: Colby College\n"
        "Ask about student life at Colby. Answers come **only** from real r/Colby "
        "threads and Rate My Professors reviews, with sources cited."
    )
    inp = gr.Textbox(label="Your question", placeholder="e.g. Do Colby dorms have air conditioning?")
    use_hybrid = gr.Checkbox(label="Use hybrid search (BM25 keyword + semantic, RRF fusion)", value=False)
    btn = gr.Button("Ask", variant="primary")
    answer = gr.Textbox(label="Answer", lines=8)
    sources = gr.Textbox(label="Sources", lines=4)
    with gr.Accordion("Retrieved chunks (what the answer is grounded in)", open=False):
        chunks = gr.Textbox(label="Top-5 chunks with cosine distances", lines=18)
    gr.Examples(examples=EXAMPLES, inputs=inp)

    btn.click(handle_query, inputs=[inp, use_hybrid], outputs=[answer, sources, chunks])
    inp.submit(handle_query, inputs=[inp, use_hybrid], outputs=[answer, sources, chunks])

if __name__ == "__main__":
    demo.launch()
