# Running the tests

## Run the automated tests

From the project root, activate the development environment:

```powershell
conda activate dev-ai
```

Run all three test suites:

```powershell
python -m pytest tests/test_ai_service.py tests/test_knowledge.py tests/test_model_history.py -v
```

If pytest is not installed in the active environment:

```powershell
python -m pip install pytest
```

## Temporary-directory permissions

If pytest reports a permission error for its default temporary directory, use a dedicated test directory:

```powershell
python -m pytest tests/test_ai_service.py tests/test_knowledge.py tests/test_model_history.py -v --basetemp="$env:TEMP\manual-assistant-tests"
```

This directory is disposable. Pytest may clear its contents, so do not store manuals or other important files there.

The ingestion fixture changes the working directory to its temporary test folder. This keeps relative file-movement operations outside the actual project data folders.

## Test scope

| Test file | Coverage |
| :--- | :--- |
| `test_ai_service.py` | Input validation, equipment parameters, evidence forwarding, latest-question retrieval, empty results, and error handling |
| `test_knowledge.py` | Invalid PDFs, chunk metadata, retrieval filters, source metadata, and empty collections |
| `test_model_history.py` | Message ordering, model selection, and preservation of the original history |

Ollama responses, embeddings, and database operations are replaced with test doubles. PDF extraction is also mocked except in the test that checks rejection of an actual invalid PDF file.

The tests do not load model weights or modify the real Chroma database. Importing application dependencies can still take time.

## Latest results

Separate runs on **2026-10-21** reported:

- **24 passed**
- **0 failed**
- **1 skipped**

Follow-up query handling, empty evidence handling, and empty-collection handling now pass. Their previous expected-failure (`xfail`) markers have been removed.

## Remaining coverage gaps

- `test_dropdown_selection_reaches_service` is still a skipped placeholder. The equipment dropdown exists, but its UI-to-service integration has not been verified by this test.
- `test_unsupported_device` needs review to ensure it passes an explicit unknown equipment selection rather than merely omitting equipment.
- Automatic folder creation, processed-file movement, filename conflicts, and dropdown refreshes need dedicated assertions. Executing those operations during another test does not fully verify their behavior.
- Service-level follow-up tests do not establish that the UI maintains a complete multi-turn conversation history.

A skipped test does not verify functionality. A passing test only verifies the behavior covered by its assertions.

## Answer-quality evaluation

Automated tests with test doubles do not measure real retrieval relevance or language-model accuracy.

Evaluate answers separately against the original manuals using [manual RAG checks](../evaluation/manual_rag_checks.md). Record those observations separately from automated test results.

See [evaluation results](../evaluation/evaluation_results.md) for the results summary and known model-answer limitations.
