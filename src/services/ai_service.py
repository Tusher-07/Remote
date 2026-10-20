
import traceback
from typing import Optional

from ollama import Client

from app.knowledge import get_search_resources, retrieve
from src.models.model_client import (
    OllamaModelClient,
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.schemas.responses import UserRequest, AIResponse


OLLAMA_HOST = "http://localhost:11434"
model_client = Client(host=OLLAMA_HOST, timeout=60.0)

installed = model_client.list().models
INSTALLED_MODELS = [item.model for item in installed]

if not INSTALLED_MODELS:
    raise RuntimeError("No Ollama models are installed.")

DEFAULT_MODEL_ID = INSTALLED_MODELS[0]


GROUNDING_INSTRUCTION = """
You are an industrial equipment manual assistant.
Use only the manual excerpts supplied with the current request.
Conversation history is context, not verified technical evidence.
If no relevant excerpts are supplied, say that you cannot verify
the answer from the manuals.
Do not invent fault meanings, repair steps, or source references.
Respond in plain text.
Cite the excerpt numbers supporting your answer, for example [1] or [2].
After your answer, include a "Sources" section.
For each excerpt used, provide its number, manual filename, page range,
and a short exact quote supporting the answer.
Only cite excerpts that support your answer.
If none of the excerpts supports an answer, state that clearly.
"""


class AIService:
    """Validate requests and generate answers grounded in equipment manuals."""

    def __init__(self, model_client: Optional[OllamaModelClient] = None):
        self.model_client = model_client

    def _get_client(self) -> OllamaModelClient:
        """Return the injected model client or create the default client."""
        if self.model_client is None:
            self.model_client = OllamaModelClient()
        return self.model_client

    def process_message(
        self,
        user_message: str,
        history=None,
        model_id=None,
        equipment=None,
    ) -> AIResponse:
        """Generate a response using evidence from the selected equipment manual."""

        if not user_message or not user_message.strip():
            return AIResponse(
                content="Please enter a message before sending.",
                success=False,
                error_message="User message was empty.",
            )

        if not history:
            return AIResponse(
                content="Please provide conversation history and select equipment.",
                success=False,
            )

        if not equipment:
            return AIResponse(
                content="Please select equipment before asking a question.",
                success=False,
            )

        try:
            manufacturer, model = equipment.split("|", 1)
            manufacturer = manufacturer.strip()
            model = model.strip()

            if not manufacturer or not model:
                raise ValueError("Manufacturer or model is missing.")

        except (AttributeError, ValueError):
            return AIResponse(
                content=(
                    "Invalid equipment selection. "
                    "Please select equipment from the dropdown."
                ),
                success=False,
            )

        try:
            request = UserRequest(message=user_message.strip())

            embedding_model, collection = get_search_resources()

            # Use the latest user question, not an older question in the chat.
            search_question = request.message

            evidence = retrieve(
                question=search_question,
                manufacturer=manufacturer,
                model=model,
                embedding_model=embedding_model,
                collection=collection,
                top_k=3,
            )

            if not evidence:
                return AIResponse(
                    content=(
                        "I couldn't find relevant information in the selected "
                        "equipment's manual. Please check the equipment selection "
                        "or the available manual."
                    ),
                    success=False,
                )
                
            print(f"\nFound chunks: {len(evidence)}", flush=True)
            for number, item in enumerate(evidence, start=1):
                print(
                    f"\n--- Chunk {number} ---\n"
                    f"Manual: {item['manual']}\n"
                    f"Pages: {item['page_start']}–{item['page_end']}\n"
                    f"{item['text']}",
                    flush=True,
                )
            evidence_text = "\n\n".join(
                f"[{number}] {item['manual']}, "
                f"pages {item['page_start']}–{item['page_end']}\n"
                f"{item['text']}"
                for number, item in enumerate(evidence, start=1)
            )

            grounded_prompt = (
                f"Question: {search_question}\n"
                f"Equipment: {manufacturer} {model}\n\n"
                f"Manual excerpts:\n{evidence_text}"
            )

            client = self._get_client()

            response_text = client.generate(
                grounded_prompt,
                history=history,
                model_id=model_id,
                system_instruction=GROUNDING_INSTRUCTION,
            )

            return AIResponse(
                content=response_text,
                success=True,
            )

        except OllamaConnectionError as err:
            return AIResponse(
                content=(
                    "[Error] Could not connect to Ollama.\n\n"
                    "Please verify that Ollama is installed and running locally."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelNotFoundError as err:
            return AIResponse(
                content=(
                    "[Error] The configured AI model is unavailable in Ollama.\n\n"
                    "Please verify your model settings or run "
                    "'ollama run <model_name>'."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelClientError as err:
            return AIResponse(
                content=(
                    "[Error] An unexpected communication error occurred "
                    "with the AI model."
                ),
                success=False,
                error_message=str(err),
            )

        except Exception as err:
            traceback.print_exc()
            return AIResponse(
                content="[Error] An unexpected application error occurred.",
                success=False,
                error_message=str(err),
            )


def generate_response(
    user_message: str,
    history=None,
    model_id=None,
    service: Optional[AIService] = None,
    equipment=None,
) -> str:
    """Return an answer grounded in the selected equipment's manual."""

    active_service = service or AIService()

    response = active_service.process_message(
        user_message,
        history=history,
        model_id=model_id,
        equipment=equipment,
    )

    return response.content
