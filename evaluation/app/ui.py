
from pathlib import Path

import gradio as gr

from src.services.ai_service import (
    generate_response,
    INSTALLED_MODELS,
    DEFAULT_MODEL_ID,
)
from app.knowledge import chunk_and_embed_pdf, get_equipment_pairs


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
        return "Please select a PDF manual.", "", gr.skip(),gr.skip()

    if not all(
        value and value.strip()
        for value in (manufacturer, model, device_type)
    ):
        return "Please fill in all three metadata fields.", "", gr.skip(), gr.skip()

    pdf_path = MANUALS_DIR / manual_name

    try:
        chunks, success = chunk_and_embed_pdf(
            str(pdf_path),
            manufacturer.strip(),
            model.strip(),
            device_type.strip(),
        )

        if success:
            manuals = get_manuals()
            equipment_choices = [
                (f"{manu} {model}", f"{manu}|{model}")
                    for manu, model in get_equipment_pairs()
                    ]
            return (
                f"Successfully processed: {manual_name}",
                f"Chunks processed: {chunks}",
                gr.Dropdown(
                    choices=manuals,
                    value=manuals[0] if manuals else None,
                    ),
                gr.Dropdown(
                    choices=equipment_choices,
                    value=f"{manufacturer.strip()}|{model.strip()}",
                    ),
            ) 
        
        return "Processing was not successful.", "", gr.skip(), gr.skip()

    except Exception as error:
        return f"Processing failed: {error}", "", gr.skip(), gr.skip()

def answer_question(message, model_id, equipment):
    """Generate an answer using the selected equipment manual."""
    if not message or not message.strip():
        return "Please enter a maintenance question."

    if not equipment:
        return "Please select equipment before asking a question."

    return generate_response(
        message.strip(),
        history=[{"role": "user", "content": message.strip()}],
        model_id=model_id,
        equipment=equipment,
    )


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

            Select a PDF and enter its equipment details.
            """
        )
        manuals = get_manuals()
        
        manual_dropdown = gr.Dropdown(
            choices=manuals,
            value=manuals[0] if manuals else None,
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

        

        gr.Markdown(
            """
            ---
            ## 🤖 2. Ask the Maintenance Assistant

            Enter a question about equipment faults, maintenance,
            or troubleshooting.
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

        model_selector = gr.Dropdown(
            choices=INSTALLED_MODELS,
            value=DEFAULT_MODEL_ID,
            label="Model",
        )

        equipment_pairs = get_equipment_pairs()

        equipment_choices = [
            (f"{manufacturer} {model}", f"{manufacturer}|{model}")
            for manufacturer, model in equipment_pairs
        ]

        equipment_selector = gr.Dropdown(
            choices=equipment_choices,
            value=equipment_choices[0][1] if equipment_choices else None,
            label="Select equipment",
            info="Choose the equipment whose manual you want to use.",
            interactive=True,
        )
        
        process_btn.click(
            fn=process_manual,
            inputs=[
                manual_dropdown,
                manufacturer_input,
                model_input,
                device_type_input,
            ],
            outputs=[
                process_status,
                chunk_status,
                manual_dropdown,
                equipment_selector,
                ],
        )

        user_input = gr.Textbox(
            lines=4,
            placeholder="Enter a fault code or maintenance question...",
            label="Maintenance Question",
            max_length=500,
        )

        output_box = gr.Textbox(
            lines=10,
            label="AI Answer",
            interactive=False,
        )

        with gr.Row():
            submit_btn = gr.Button(
                "🤖 Ask Assistant",
                variant="primary",
            )

            clear_btn = gr.ClearButton(
                [user_input, output_box],
                value="🧹 Clear",
                variant="secondary",
            )

        submit_btn.click(
            fn=answer_question,
            inputs=[user_input, model_selector, equipment_selector],
            outputs=output_box,
        )

        user_input.submit(
            fn=answer_question,
            inputs=[user_input, model_selector, equipment_selector],
            outputs=output_box,
        )

    return demo
