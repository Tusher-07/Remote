import gradio as gr
from src.services.ai_service import generate_response
from ai_service import DEFAULT_MODEL_ID, INSTALLED_MODELS, ai_service


def content_to_text(content):
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )

    return ""


def history_for_service(history):
    converted = []

    for message in history:
        role = message.get("role")
        text = content_to_text(message.get("content"))

        if role in {"user", "assistant"} and text:
            converted.append({"role": role, "content": text})

    return converted


def format_sources(result):
    if result["reply"].evidence_status == "insufficient":
        return "No cited source: the retrieved passages did not contain enough evidence."

    blocks = []

    for number, source in zip(result["reply"].citations, result["sources"]):
        blocks.append(
            f"**[{number}] {source['title']} — page {source['page']}**\n\n"
            f"{source['text']}"
        )

    return "\n\n---\n\n".join(blocks)


def chat_reply(message, history, model_id):
    result = ai_service(
        message,
        history_for_service(history),
        model_id=model_id,
    )

    if result["status"] == "error":
        return result["message"], {"status": "error"}, "No sources."

    reply = result["reply"]

    metadata = {
        "model": result["model"],
        "category": reply.category,
        "needs_human": reply.needs_human,
        "evidence_status": reply.evidence_status,
        "citations": reply.citations,
    }

    return reply.answer, metadata, format_sources(result)




def build_ui() -> gr.Blocks:
    """
    Builds the Gradio interface for the AI Maintenance Manual Assistant.
    """

    with gr.Blocks(title="AI Maintenance Manual Assistant") as demo:

        gr.Markdown(
            """
            # 🔧 AI Maintenance Manual Assistant

            Ask questions about industrial equipment, fault codes,
            maintenance, and troubleshooting.
            """
        )

        gr.Markdown(
            """
            **Example questions:**
            - What does fault code F1 mean?
            - How can I troubleshoot this fault?
            - What should I check before restarting the machine?
            """
        )

        user_input = gr.Textbox(
            lines=4,
            placeholder="Enter a fault code or maintenance question...",
            label="Maintenance Question",
            max_length=500,
        )

        with gr.Row():
            submit_btn = gr.Button("Ask Assistant", variant="primary")
            clear_btn = gr.ClearButton([user_input])

        output_box = gr.Textbox(
            lines=10,
            label="AI Answer",
            interactive=False,
        )

        submit_btn.click(
            fn=generate_response,
            inputs=user_input,
            outputs=output_box,
        )

        user_input.submit(
            fn=generate_response,
            inputs=user_input,
            outputs=output_box,
        )

    return demo

if __name__ == "__main__":
    demo.launch(share=False)
    
    
    
