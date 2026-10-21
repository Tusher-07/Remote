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

---

## Decision 4 — Equipment selection

**Decision:**  
Allow users to select equipment from a dropdown populated with manufacturer–model pairs stored in Chroma. Pass the selected manufacturer and model to retrieval as metadata filters.

**Alternatives considered:**  
Asking users to type equipment details into the conversation and extracting the manufacturer and model from their response.

**Why we chose this:**  
A dropdown reduces typing errors and limits selections to equipment represented in the indexed data. It also avoids relying on the language model to interpret equipment names.

The dropdown does not prevent incorrect metadata during manual ingestion. Correcting stored metadata remains a future improvement.

---

## Decision 5 — Managing processed PDF files

**Decision:**  
After successful indexing, attempt to move the PDF from `data/Manuals` to `data/Processed manuals`. Create the destination folder if necessary and do not overwrite an existing file with the same name.

Refresh both the PDF and equipment dropdowns after successful processing.

**Alternatives considered:**  
Keeping all PDFs in the same folder and tracking their processing status separately.

**Why we chose this:**  
Separating processed files makes the processing list easier to use and helps users distinguish pending manuals from previously processed files.

Indexed content remains in Chroma independently of the PDF’s location. Moving or deleting a PDF does not delete its indexed content.

**Trade-offs:**  
The filename check occurs after indexing, so duplicate processing can still repeat embedding computation. If the destination file already exists, the source PDF remains in the input folder. Editing metadata and deleting indexed manuals are not yet supported through the UI.
