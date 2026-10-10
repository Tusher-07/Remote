import gradio as gr
from src.services.ai_service import generate_response


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
    demo = build_ui()
    demo.launch()