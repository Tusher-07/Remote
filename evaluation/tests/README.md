# Running the tests

From the project root in the dev-ai environment:

    python -m pytest tests/test_ai_service.py tests/test_knowledge.py tests/test_model_history.py -v

Ollama responses, embeddings, PDF extraction (except the corrupt-PDF check),
and database access are replaced with test doubles. No real models are loaded
and no real Chroma data is modified.

Known gaps are explicit:
- strict xfail: follow-up handling, empty evidence handling, empty collection.
- skip: future dropdown-to-service integration, whose interface does not exist.
An XPASS is a failure: after implementing the feature, remove its xfail marker.
A skipped placeholder does not verify functionality.

Real answer quality must be evaluated separately using
evaluation/manual_rag_checks.md. Keep those results separate from unit tests.
