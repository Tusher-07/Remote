# Architecture Documentation

This document describes the architecture of the AI Maintenance Manual Assistant. The application uses Retrieval-Augmented Generation (RAG) to answer equipment questions using locally stored maintenance manuals.

## Application Architecture

```text
User
  ↓
Gradio UI (app/ui.py)
  ↓
Application / AI Service (src/services/ai_service.py)
  ├── Manual Retrieval (app/knowledge.py)
  │     ↓
  │   BGE-M3 Query Embedding
  │     ↓
  │   Chroma Vector Database
  │   Filter by manufacturer and model
  │     ↓
  │   Relevant manual excerpts and source metadata
  │
  └── Grounded Prompt
        Question + conversation history + manual excerpts
        ↓
      Model Client (src/models/model_client.py)
        ↓
      Ollama (Local Inference Server)
        ↓
      Qwen3.5:9b
        ↓
      Response returned through the service to the UI
```

## Manual Processing

Manual ingestion is separate from answering questions. Each PDF is processed with equipment metadata supplied by the user.

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
```

Each stored chunk contains its text and metadata identifying the manual, manufacturer, equipment model, device type, and page range. Chroma stores the data under `data/chroma`, allowing it to remain available after the application restarts.

The same embedding model is used for both manual chunks and search queries.

## Component Responsibilities

### User Interface

`app/ui.py` provides the Gradio interface for manual processing and questions. It collects user input and displays processing results and assistant responses.

### Application Service

`src/services/ai_service.py` coordinates question handling. It validates input, obtains equipment details, requests relevant manual excerpts, and constructs the grounded prompt before calling the model client.

It also converts failures into user-facing messages.

### Manual Processing and Retrieval

`app/knowledge.py` contains PDF ingestion, chunking, embedding generation, database access, and retrieval.

Retrieval filters the stored chunks by manufacturer and equipment model, then searches for text relevant to the question. Results include the manual filename and page range.

### Model Client

`src/models/model_client.py` manages communication with Ollama. It passes the selected model, system instruction, conversation history, and grounded question to the local server.

It handles communication failures and missing-model errors.

### Local Models

`BAAI/bge-m3` generates embeddings for semantic retrieval. `qwen3.5:9b`, served through Ollama, generates answers from the retrieved excerpts. These models perform different tasks.

## Core Design Rules

1. **UI Isolation:** The UI must not communicate directly with the model client or Ollama. Model requests pass through the application service.
2. **Evidence-Based Responses:** The model is instructed to answer using only the supplied manual excerpts. Conversation history provides context but is not verified technical evidence.
3. **Equipment Filtering:** Retrieval must use the selected equipment’s manufacturer and model to avoid mixing instructions from different devices.
4. **Controlled Failure Handling:** Technical failures are converted into understandable application responses.
5. **Data Validation:** Pydantic models in `src/schemas/responses.py` validate request and response structures. They do not verify the factual accuracy of generated answers.

## Current Limitations and Planned Improvements

- PDF processing extracts text but does not interpret diagrams or images. Important information may therefore be missing from retrieved excerpts.
- Grounding reduces unsupported answers but does not guarantee accuracy. Answers must be evaluated&#x20;
- Follow-up handling must ensure that retrieval uses the current question while retaining the selected equipment.
- Source metadata is available from retrieval; consistent source references in the displayed answer still require verification.
- RAG functionality may later be moved from `app/knowledge.py` into `src/capabilities/rag.py`, with imports and database paths updated accordingly.

## Testing

Automated tests cover input validation, retrieval parameters, evidence forwarding, conversation-history ordering, PDF processing, metadata preservation, and error handling.

Known incomplete features are marked explicitly in the test suite. Answer quality is evaluated separately against the original manuals using `evaluation/manual_rag_checks.md`.
