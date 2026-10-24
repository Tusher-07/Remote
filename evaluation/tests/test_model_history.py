from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock
from src.models.model_client import OllamaModelClient

def test_history_order_and_selected_model(monkeypatch):
    transport = MagicMock()
    transport.chat.return_value = SimpleNamespace(message=SimpleNamespace(content="answer"))
    monkeypatch.setattr("src.models.model_client.ollama.Client", MagicMock(return_value=transport))
    client = OllamaModelClient(base_url="http://test.invalid", model_name="default")
    history = [{"role": "user", "content": "first"},
               {"role": "assistant", "content": "second"}]
    original = deepcopy(history)
    assert client.generate("new question", history=history,
        model_id="selected", system_instruction="Use evidence only.") == "answer"
    kwargs = transport.chat.call_args.kwargs
    assert kwargs["model"] == "selected"
    assert kwargs["messages"] == [
        {"role": "system", "content": "Use evidence only."},
        *original, {"role": "user", "content": "new question"}]
    assert history == original
