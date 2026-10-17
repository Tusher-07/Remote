"""Service tests use fake model responses and retrieval results."""
import importlib
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import pytest

@pytest.fixture
def case(monkeypatch):
    with patch("ollama.Client.list", return_value=SimpleNamespace(
        models=[SimpleNamespace(model="test-model")]
    )):
        module = importlib.import_module("src.services.ai_service")
    embedding, collection, client = MagicMock(), MagicMock(), MagicMock()
    collection.get.return_value = {"metadatas": [{"manufacturer": "Vacon", "model": "100"}]}
    resources = MagicMock(return_value=(embedding, collection))
    evidence = [{"id": "1", "manual": "test.pdf", "page_start": 7,
                 "page_end": 8, "text": "TEST EVIDENCE: inspect the indicator."}]
    retrieve = MagicMock(return_value=evidence)
    monkeypatch.setattr(module, "get_search_resources", resources)
    monkeypatch.setattr(module, "retrieve", retrieve)
    client.generate.return_value = "Test answer."
    return SimpleNamespace(module=module, service=module.AIService(model_client=client),
        client=client, retrieve=retrieve, resources=resources, evidence=evidence,
        embedding=embedding, collection=collection,
        history=[{"role": "user", "content": "How do I inspect the device?"},
                 {"role": "assistant", "content": "Which device?"}])

def test_config_loading():
    from src.config import config
    assert isinstance(config.ollama_base_url, str) and config.ollama_base_url
    assert isinstance(config.model_name, str) and config.model_name

@pytest.mark.parametrize("message", ["", "   ", None])
def test_empty_input_validation(case, message):
    response = case.service.process_message(message)
    assert response.success is False
    assert "Please enter a message" in response.content
    case.client.generate.assert_not_called()
    case.resources.assert_not_called()

def test_missing_device(case):
    response = case.service.process_message("What does this fault mean?")
    assert "manufacturer and model" in response.content
    case.retrieve.assert_not_called()
    case.client.generate.assert_not_called()

def test_unsupported_device(case):
    response = case.service.process_message("Siemens G120", history=case.history)
    assert response.success is False
    case.retrieve.assert_not_called()
    case.client.generate.assert_not_called()

def test_device_and_question_reach_retrieval(case):
    case.service.process_message(" VACON 100 ", history=case.history)
    case.retrieve.assert_called_once_with(
        question=case.history[0]["content"], manufacturer="Vacon", model="100",
        embedding_model=case.embedding, collection=case.collection, top_k=3)

def test_successful_response_and_grounding(case):
    result = case.module.generate_response("Vacon 100", history=case.history,
        model_id="selected-model", service=case.service)
    assert result == "Test answer."
    case.client.generate.assert_called_once()
    args, kwargs = case.client.generate.call_args
    assert case.history[0]["content"] in args[0]
    assert case.evidence[0]["text"] in args[0]
    assert "test.pdf" in args[0]
    assert "7–8" in args[0]
    assert kwargs["history"] == case.history
    assert kwargs["model_id"] == "selected-model"
    assert kwargs["system_instruction"] == case.module.GROUNDING_INSTRUCTION

@pytest.mark.parametrize("error_type, expected", [
    ("OllamaConnectionError", "Could not connect to Ollama"),
    ("ModelNotFoundError", "configured AI model is unavailable"),
    ("ModelClientError", "communication error"),
])
def test_model_error_handling(case, error_type, expected):
    case.client.generate.side_effect = getattr(case.module, error_type)("test failure")
    response = case.service.process_message("Vacon 100", history=case.history)
    assert response.success is False
    assert expected in response.content
    assert "test failure" in response.error_message

def test_retrieval_error(case):
    case.retrieve.side_effect = RuntimeError("database unavailable")
    response = case.service.process_message("Vacon 100", history=case.history)
    assert response.success is False
    assert "database unavailable" in response.error_message
    case.client.generate.assert_not_called()

@pytest.mark.xfail(strict=True, reason="Follow-up is currently treated as a device name.")
def test_followup_uses_latest_question(case):
    history = case.history + [
        {"role": "user", "content": "Vacon 100"},
        {"role": "assistant", "content": "Previous grounded answer."}]
    case.service.process_message("What should I check next?", history=history)
    case.retrieve.assert_called_once()
    assert case.retrieve.call_args.kwargs["question"] == "What should I check next?"

@pytest.mark.xfail(strict=True, reason="Empty evidence currently still reaches the model.")
def test_no_evidence_notice_without_model_call(case):
    case.retrieve.return_value = []
    response = case.service.process_message("Vacon 100", history=case.history)
    case.client.generate.assert_not_called()
    assert response.content.strip()
    assert response.content != "Test answer."

@pytest.mark.skip(reason="Device dropdown interface is not implemented yet.")
def test_dropdown_selection_reaches_service():
    """Replace with an actual UI integration test once the interface exists."""
