from pathlib import Path

import gradio as gr

from src.services.ai_service import generate_response
from app.knowledge import chunk_and_embed_pdf


MANUALS_DIR = Path(__file__).resolve().parent.parent / "data" / "Manuals"


def get_manuals():
    """Find available PDF manuals."""
    if not MANUALS_DIR.is_dir():
        return []

    return sorted(
        path.name
        for path in MANUALS_DIR.glob("*.pdf")
        if path.is_file()
    )


def process_manual(manual_name, manufacturer, model, device_type):
    """Validate the form and process the selected manual."""
    if not manual_name:
        return "Please select a PDF manual.", ""

    if not all(
        value and value.strip()
        for value in (manufacturer, model, device_type)
    ):
        return "Please fill in all three metadata fields.", ""

    pdf_path = MANUALS_DIR / manual_name

    try:
        chunks, success = chunk_and_embed_pdf(
            str(pdf_path),
            manufacturer.strip(),
            model.strip(),
            device_type.strip(),
        )

        if success:
            return (
                f"Successfully processed: {manual_name}",
                f"Chunks processed: {chunks}",
            )

        return "Processing was not successful.", ""

    except Exception as error:
        return f"Processing failed: {error}", ""


def build_ui() -> gr.Blocks:
    """Build the maintenance assistant interface."""
    with gr.Blocks(
        title="AI Maintenance Manual Assistant",
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
        neutral_hue="slate",
    ),
    css="""
    .gradio-container {
        max-width: 1100px !important;
        margin: auto !important;
    }
    """,
) as demo:
        gr.Markdown(
            """
            # 🔧 AI Maintenance Manual Assistant

            Ask questions about industrial equipment, fault codes,
            maintenance, and troubleshooting.
            """
        )

        gr.Markdown(
    """
    ---
    ## 📄 1. Process a Maintenance Manual
    Upload selection and equipment details are used to process the chosen PDF manual.
    """
)

        manual_dropdown = gr.Dropdown(
            choices=get_manuals(),
            label="Select PDF manual",
            interactive=True,
        )

        with gr.Row():
            manufacturer_input = gr.Textbox(
                label="Manufacturer",
                placeholder="e.g. VACON",
            )
            model_input = gr.Textbox(
                label="Model",
                placeholder="e.g. VACON 100",
            )
            device_type_input = gr.Textbox(
                label="Device type",
                placeholder="e.g. Variable frequency drive",
            )

        process_btn = gr.Button(
    "⚙️ Process Manual",
    variant="primary",
    size="lg",
)

        process_status = gr.Textbox(
            label="Processing status",
            interactive=False,
        )
        chunk_status = gr.Textbox(
            label="Processing result",
            interactive=False,
        )

        process_btn.click(
            fn=process_manual,
            inputs=[
                manual_dropdown,
                manufacturer_input,
                model_input,
                device_type_input,
            ],
            outputs=[process_status, chunk_status],
        )

        gr.Markdown(
    """
    ---
    ## 🤖 2. Ask the Maintenance Assistant
    Enter a question about equipment faults, maintenance, or troubleshooting.
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
            submit_btn = gr.Button(
                "🤖 Ask Assistant",
                variant="primary",
                size="lg",
            )
            clear_btn = gr.Button(
                "🧹 Clear",
                variant="secondary",
                size="lg",
            )

        output_box = gr.Textbox(
            lines=10,
            label="AI Answer",
            interactive=False,
        )


        clear_btn.click(
            fn=lambda: ("", ""),
            inputs=None,
            outputs=[user_input, output_box],
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
