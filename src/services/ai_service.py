import traceback

from numpy import number
from app.knowledge import retrieve, get_search_resources
from ollama import Client
from typing import Optional
from src.models.model_client import (
    OllamaModelClient,
    ModelClientError,
    OllamaConnectionError,
    ModelNotFoundError,
)
from src.schemas.responses import UserRequest, AIResponse

from app.knowledge import retrieve, get_search_resources

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
"""


class AIService:
    """
    Application service layer responsible for validating user input,
    orchestrating model client requests, and catching exceptions gracefully.
    """

    def __init__(self, model_client: Optional[OllamaModelClient] = None):
        # Allow injecting custom/mock model_client for simple testing
        self.model_client = model_client

    def _get_client(self) -> OllamaModelClient:
        """Returns active model client, initializing default client if none provided."""
        if self.model_client is None:
            self.model_client = OllamaModelClient()
        return self.model_client

    def process_message(self, user_message: str, history=None, model_id=None) -> AIResponse:
        """
        Processes a raw user message string and returns a structured AIResponse.
        Catches technical failures and converts them to friendly user-facing messages.
        """
        # 1. Validate empty input
        if not user_message or not user_message.strip():
            return AIResponse(
                content="Please enter a message before sending.",
                success=False,
                error_message="User message was empty.",
            )
        if not history:
            return AIResponse(
                content="Please provide device manufacturer and model.",
                success=True,
            )
                
        try:
            # 2. Schema validation
            request = UserRequest(message=user_message.strip())

            # 3. Call model client
            
            print("Before model call", flush=True)
            
            client = self._get_client()
            
            if request.message.strip().lower() != "vacon 100":
                            return AIResponse(
                                content="Currently, only 'Vacon 100' is supported as a device model.",
                                success=False,
                            )
                            
            
            embedding_model, collection = get_search_resources()
            
            stored = collection.get(include=["metadatas"])

            equipment_pairs = {
                (metadata["manufacturer"], metadata["model"])
                for metadata in stored["metadatas"]
                }
            equipment_pairs_list = [
                f"{manu} {model}"
                for manu, model in sorted(equipment_pairs)
            ]


                   
            search_question = history[0]["content"]
            
            evidence = retrieve(
                question=search_question,
                #manufacturer=history[0].get("manufacturer") if history else None,
                manufacturer="Vacon",
                #model=history[0].get("model") if history else None,
                model="100",
                embedding_model=embedding_model,
                collection=collection,  
                top_k=3
            )
         
            for number, item in enumerate(evidence, start=1):
                print(
                f"\n--- Katkelma {number} ---\n"
                f"Manuaali: {item['manual']}\n"
                f"Sivut: {item['page_start']}–{item['page_end']}\n"
                f"{item['text']}\n"
    )

            evidence_text = "\n\n".join(
                f"[{number}] {item['manual']}, "
                f"pages {item['page_start']}–{item['page_end']}\n"
                f"{item['text']}"
                for number, item in enumerate(evidence, start=1)
            )
            grounded_prompt = (
                f"Question: {search_question}\n"
                f"Equipment: {request.message}\n\n"
                f"Manual excerpts:\n{evidence_text}"
)

            response_text = client.generate(
                #request.message, 
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
                    "Please verify that Ollama is installed and running locally on your machine."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelNotFoundError as err:
            return AIResponse(
                content=(
                    f"[Error] The configured AI model is unavailable in Ollama.\n\n"
                    f"Please verify your MODEL_NAME setting or run 'ollama run <model_name>'."
                ),
                success=False,
                error_message=str(err),
            )

        except ModelClientError as err:
            return AIResponse(
                content="[Error] An unexpected communication error occurred with the AI model.",
                success=False,
                error_message=str(err),
            )

        except Exception as err:
                import traceback
                traceback.print_exc()
                return AIResponse(
                    content="[Error] An unexpected application error occurred.",
                    success=False,
                    error_message=str(err),
                )


def generate_response(user_message: str, history = None, model_id=None, service: Optional[AIService] = None) -> str:
    """
    Main reusable service entry point used by the UI layer.
    
    Accepts user input message, passes it to the AI service, and returns
    the generated text response (or a friendly error message).
    """
    active_service = service or AIService()
    response = active_service.process_message(
        user_message,
        history=history,
        model_id=model_id
    )
    return response.content
