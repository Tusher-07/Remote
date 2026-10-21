# Architecture Documentation

This document describes the architecture of the AI Maintenance Manual Assistant. The application uses Retrieval-Augmented Generation (RAG) to answer equipment questions using locally stored maintenance manuals.

## Application Architecture

```text
User
  ↓
Gradio UI (app/ui.py)
  Question + equipment selection + model selection
  ↓
Application / AI Service (src/services/ai_service.py)
  ├── Manual Retrieval (app/knowledge.py)
  │     ↓
  │   BGE-M3 Query Embedding
  │     ↓
  │   Chroma Vector Database
  │   Filter by manufacturer and equipment model
  │     ↓
  │   Relevant excerpts and source metadata
  │
  └── Grounded Prompt
        Question + supplied history + manual excerpts
        ↓
      Model Client (src/models/model_client.py)
        ↓
      Ollama (Local Inference Server)
        ↓
      User-selected model, e.g. qwen3.5:9b
        ↓
      Response returned through the service to the UI
```

The equipment selection identifies which manuals to search. The model selection identifies which installed Ollama model generates the answer. These are independent selections.

## Manual Processing

Manual ingestion is separate from answering questions. Each PDF is processed with manufacturer, equipment model, and device-type metadata supplied by the user.

```text
PDF Manual + Manufacturer + Model + Device Type
  ↓
Manual Processing (app/knowledge.py)
  ↓
Text Extraction with pypdf
  ↓
Text Chunking with Page References
  ↓
Embeddings with BAAI/bge-m3
  ↓
Persistent Chroma Collection
maintenance_manuals_bge_m3
  ↓
Attempt to move PDF to data/Processed manuals
  ↓
Refresh PDF and equipment dropdowns
```

The destination folder is created if necessary. If a file with the same name already exists there, the move is skipped without overwriting it. The source PDF remains available in the processing dropdown.

Indexing occurs before the file move. Therefore, an indexing success and a file-movement failure are separate outcomes.

Each stored chunk contains its text and metadata identifying the manual, manufacturer, equipment model, device type, and page range. Chroma stores its data under `data/chroma`, allowing indexed content to remain available after the application restarts.

Moving or deleting an original PDF does not remove its indexed content from Chroma.

## Component Responsibilities

### User Interface

`app/ui.py` provides the Gradio interface for manual processing and questions.

It:

- Lists PDF files available in `data/Manuals`.
- Collects metadata for manual processing.
- Calls the manual-processing function and displays its result.
- Builds the equipment dropdown from manufacturer–model pairs stored in Chroma.
- Refreshes the PDF and equipment dropdowns after successful processing.
- Passes the question, selected equipment, and selected response model to the application service.
- Displays the returned answer.

The UI currently calls manual-processing helpers in `app/knowledge.py`. Language-model requests pass through the application service.

### Application Service

`src/services/ai_service.py` coordinates question handling. It validates input and equipment selection, requests relevant excerpts, and constructs the grounded prompt before calling the model client.

If retrieval returns no excerpts, the service returns an informational response without calling the language model.

The service also converts technical failures into user-facing messages.

### Manual Processing and Retrieval

`app/knowledge.py` contains PDF ingestion, chunking, embedding generation, database access, equipment-list generation, and retrieval.

Retrieval uses the question embedding together with manufacturer and model filters. Results include the chunk identifier, text, manual filename, page range, and distance.

An empty collection returns an empty result before embedding generation or a database query.

### Model Client

`src/models/model_client.py` manages communication with Ollama. It constructs messages containing the system instruction, any supplied history, and the current grounded prompt.

It sends the request to the selected model and handles communication failures and missing-model errors.

### Data Schemas

Pydantic models in `src/schemas/responses.py` define request and response structures.

These schemas validate data structure and types. They do not establish whether a generated answer is factually correct.

## Local Models

### Embedding Model

`BAAI/bge-m3` generates embeddings for both manual chunks and search queries. Using the same embedding model keeps query and document vectors compatible.

The response-model dropdown does not change the embedding model.

### Response Model

The user selects from models installed in the local Ollama instance. Tested models include `qwen3.5:2b`, `qwen3.5:4b`, and `qwen3.5:9b`.

The selected model generates an answer from the retrieved excerpts. Response speed depends on the model and available hardware.

## Conversation Context

The service and model client accept conversation history. Automated tests confirm that the model client preserves message order and that retrieval uses the latest question.

However, the current question-and-answer UI does not establish a complete persistent multi-turn conversation. Service-level history support should not be confused with a fully implemented conversational interface.

## Core Design Rules

1. **Model Access Through the Service:** The UI must not communicate directly with the model client or Ollama. Model requests pass through the application service.
2. **Evidence-Based Responses:** The model is instructed to answer using only the supplied excerpts. Conversation history provides context but is not verified technical evidence.
3. **Equipment Filtering:** Retrieval uses the selected manufacturer and equipment model to avoid mixing instructions from different devices.
4. **Controlled Failure Handling:** Technical failures are converted into understandable application responses.
5. **Persistent Storage:** Indexed manual content remains available independently of the original PDF’s location.
6. **Verifiable Sources:** Retrieved excerpts retain source metadata so answers can be checked against the original manuals.

## Current Limitations and Planned Improvements

- PDF processing extracts text but does not interpret diagrams or images.
- Extracted tables may lose their structure. The model can misinterpret a table even when the correct information is present.
- Grounding and source citations do not guarantee accuracy. Answers must be checked against the original manuals.
- Stored metadata cannot yet be corrected through the UI, and indexed manuals cannot yet be deleted through it.
- The duplicate-filename check occurs after indexing and does not prevent repeated embedding computation.
- File movement and dropdown refreshes need dedicated automated tests.
- Startup with an empty or missing Chroma collection requires separate verification. Handling an empty retrieval collection does not establish that initial database creation works.
- RAG functionality may later be moved from `app/knowledge.py` into `src/capabilities/rag.py`. Imports and paths derived from file locations must be updated during that change.

## Testing

Automated tests cover input validation, retrieval parameters, evidence forwarding, conversation-history ordering, PDF processing, metadata preservation, empty-collection handling, and error handling.

Separate runs on 2026-10-21 reported **24 passed tests and one skipped test**. The skipped test is a dropdown integration placeholder. The unsupported-device test also needs review to ensure it checks an explicit unknown equipment selection.

The automated tests use test doubles and do not measure live model accuracy or real retrieval relevance. Answer quality is evaluated separately against the original manuals.

See:

- [Evaluation results](../evaluation/evaluation_results.md)
- [Manual RAG evaluation checks](../evaluation/manual_rag_checks.md)
- [Test instructions](../tests/README.md)
