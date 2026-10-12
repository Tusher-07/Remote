from typing import Literal

from ollama import Client
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from knowledge import retrieve

OLLAMA_HOST = "http://localhost:11434"
model_client = Client(host=OLLAMA_HOST, timeout=60.0)

installed = model_client.list().models
INSTALLED_MODELS = [item.model for item in installed]

if not INSTALLED_MODELS:
    raise RuntimeError("No Ollama models are installed.")

DEFAULT_MODEL_ID = INSTALLED_MODELS[0]

GROUNDING_INSTRUCTION = """You are a university support assistant used for teaching.
Answer the user's question using only the supplied evidence.
Do not invent facts that are missing from the evidence.

If the evidence supports the answer:
- set evidence_status to supported;
- cite the relevant evidence numbers.

If the evidence does not contain enough information:
- say that the supplied documents do not contain enough information;
- set evidence_status to insufficient;
- return an empty citations list;
- set needs_human to true.

Choose category course, account, or other.
Return only the structured response requested by the schema.
"""


class GroundedReply(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        str_strip_whitespace=True,
    )

    answer: str = Field(min_length=1, max_length=600)
    category: Literal["course", "account", "other"]
    needs_human: bool
    evidence_status: Literal["supported", "insufficient"]
    citations: list[int] = Field(default_factory=list, max_length=3)


def build_grounded_messages(question, evidence, history=None):
    history = history or []

    selected_history = [
        {"role": item["role"], "content": item["content"]}
        for item in history[-4:]
        if item.get("role") in {"user", "assistant"} and item.get("content")
    ]

    evidence_text = "\n\n".join(
        f"[{number}] {item['text']}"
        for number, item in enumerate(evidence, start=1)
    )

    return [
        {"role": "system", "content": GROUNDING_INSTRUCTION},
        *selected_history,
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Evidence:\n{evidence_text}"
            ),
        },
    ]


def ai_service(question, history=None, model_id=DEFAULT_MODEL_ID, course="DEV-AI"):
    cleaned = (question or "").strip()

    if not cleaned:
        return {"status": "error", "message": "Please enter a question."}

    evidence = retrieve(cleaned, course=course, top_k=3)

    try:
        response = model_client.chat(
            model=model_id,
            messages=build_grounded_messages(cleaned, evidence, history),
            format=GroundedReply.model_json_schema(),
            options={"temperature": 0, "num_predict": 300},
            stream=False,
        )

        reply = GroundedReply.model_validate_json(response.message.content or "")

        if any(number < 1 or number > len(evidence) for number in reply.citations):
            return {
                "status": "error",
                "message": "The model returned an invalid source reference.",
            }

        sources = [evidence[number - 1] for number in reply.citations]

        return {
            "status": "ok",
            "reply": reply,
            "sources": sources,
            "retrieved": evidence,
            "model": model_id,
        }

    except ValidationError:
        return {
            "status": "error",
            "message": "The model returned an invalid structured response.",
        }

    except Exception:
        return {
            "status": "error",
            "message": "The RAG service could not complete the request.",
        }
