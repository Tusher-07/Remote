# Project decisions

This decision log documents the main technical and architectural choices made during development.

## Decision 1 — Model selection

**Decision:**  
Run the response model locally through Ollama and allow the user to select from installed models in the Gradio interface. Models tested include `qwen3.5:2b`, `qwen3.5:4b`, and `qwen3.5:9b`.

Use `BAAI/bge-m3` as the embedding model for both manual indexing and retrieval. It is independent of the user-selected response model.

**Alternatives considered:**  
Using a single fixed response model or smaller local models for faster responses. For embeddings, we initially tested `sentence-transformers/all-MiniLM-L6-v2`.

**Why we chose this:**  
Local inference avoids dependence on an external LLM API. Model selection allows users to compare response quality and speed on their hardware. The 9B model was slow when running partly on the CPU, so smaller models remain useful alternatives.

The initial embedding model’s input limit was too short for our manual chunks. BGE-M3 supports longer inputs and accommodated the chunks tested.

---

## Decision 2 — Additional AI capability

**Decision:**  
Implement Retrieval-Augmented Generation (RAG) using PDF text extraction, chunking, BGE-M3 embeddings, and a persistent Chroma vector database. RAG is already in use.

**Why it is needed:**  
The application must answer questions about specific equipment using maintenance manuals. Early tests without retrieved evidence produced unsupported equipment and fault-code explanations.

RAG supplies relevant manual excerpts to the response model. Retrieval filters by manufacturer and equipment model, and the prompt instructs the model to acknowledge insufficient evidence rather than invent an answer. This reduces unsupported responses but does not guarantee accuracy.

**Alternatives considered:**  
Using the language model without retrieval or manually copying relevant manual sections into each prompt.

---

## Decision 3 — Architecture

**Decision:**  
Keep the Gradio UI, application service, model client, and manual-processing functionality separate.

- `app/ui.py` handles user interaction.
- `src/services/ai_service.py` coordinates validation, retrieval, prompt construction, and responses.
- `src/models/model_client.py` handles communication with Ollama.
- `app/knowledge.py` handles PDF processing, embeddings, Chroma storage, and retrieval.

Model requests pass through the service layer. RAG functionality may later be moved into `src/capabilities/rag.py`.

**Why:**  
Separating responsibilities makes the application easier to understand, test, and develop as a team. The UI can change without rewriting model communication, and retrieval can be improved independently.

Persistent storage allows processed manuals to remain available after restarting the application. Tests can replace model and database operations with test doubles, allowing application logic to be checked without running inference or modifying the real database.
