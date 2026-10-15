import gradio as gr
from src.services.ai_service import generate_response
from ai_service import DEFAULT_MODEL_ID, INSTALLED_MODELS, ai_service




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



# def chat_reply(message, history, model_id):
#     result = ai_service(
#         message,
#         history_for_service(history),
#         model_id=model_id,
#     )

#     if result["status"] == "error":
#         return result["message"], {"status": "error"}, "No sources."

#     reply = result["reply"]

#     metadata = {
#         "model": result["model"],
#         "category": reply.category,
#         "needs_human": reply.needs_human,
#         "evidence_status": reply.evidence_status,
#         "citations": reply.citations,
#     }

#     return reply.answer, metadata, format_sources(result)


with gr.Blocks(title="University Support Assistant — Chapter 4") as demo:
    gr.Markdown("# University Support Assistant")

    model_selector = gr.Dropdown(
        choices=INSTALLED_MODELS,
        value=DEFAULT_MODEL_ID,
        label="Model",
    )

    metadata = gr.JSON(label="Response information")
    sources = gr.Markdown(label="Sources")

    # gr.ChatInterface(
    #     fn=chat_reply,
    #     additional_inputs=[model_selector],
    #     additional_outputs=[metadata, sources],
    # )
