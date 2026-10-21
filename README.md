# AI Maintenance Manual Assistant for Industrial Equipment

## Team members

- Budhathoki Tika (tika.budhathoki@student.hamk.fi)
- Tusher Monjurul (monjurul.tusher@student.hamk.fi)
- Amil Mahfuj (mahfuj.amil@student.hamk.fi)
- Petri Suopanki (petri.suopanki@student.hamk.fi)

## Problem

### Intended users

The application is intended for industrial maintenance personnel and equipment operators who need information about equipment faults, operation, and maintenance.

### Problem statement

Finding relevant instructions in lengthy, equipment-specific manuals can be time-consuming. Paper manuals may also be missing or unavailable. The application helps users search stored digital manuals and obtain answers with source references.

### Why AI is appropriate

A language model supports natural-language questions and can combine information from multiple manual excerpts into an understandable answer. Retrieval-Augmented Generation (RAG) supplies equipment-specific evidence instead of relying only on the model’s general knowledge.

## Solution

The prototype combines a Gradio interface, locally stored PDF manuals, a persistent Chroma vector database, and a language model running through Ollama.

Users can process manuals, select equipment, and ask questions. The application retrieves relevant excerpts from the selected equipment’s manuals and supplies them to the model.

Automated web search is outside the scope of the current version. Generated answers require verification against the original manual before being used for maintenance decisions.

## Main user workflow

### Processing a manual

1. Place a PDF in `data/Manuals`.
2. Select the PDF in the interface.
3. Enter the manufacturer, equipment model, and device type.
4. Select **Process Manual**.
5. The application extracts text, creates chunks, generates embeddings, and stores the results in Chroma.
6. After successful indexing, the application attempts to move the PDF to `data/Processed manuals`. The folder is created if necessary. An existing file with the same name is not overwritten.
7. The PDF and equipment dropdown menus are refreshed.

If a filename conflict prevents the move, the source PDF remains in `data/Manuals` and remains available in the PDF dropdown.

### Asking a question

1. Select an installed Ollama model.
2. Select equipment from the devices represented in the indexed manuals.
3. Enter a fault code or maintenance question.
4. The service validates the input and retrieves relevant excerpts filtered by manufacturer and equipment model.
5. The model receives the question, retrieved excerpts, and grounding instructions.
6. The interface displays the answer. The model is instructed to cite supporting excerpts and acknowledge insufficient evidence.

## Architecture

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

Model requests pass through the application service. The UI must not communicate directly with the model client or Ollama.

### Component responsibilities

| Component | Responsibility |
| :--- | :--- |
| `app/ui.py` | Collects user input, handles selections, and displays processing results and answers. |
| `src/services/ai_service.py` | Validates requests, coordinates retrieval, constructs grounded prompts, and handles application errors. |
| `app/knowledge.py` | Extracts PDF text, creates chunks and embeddings, manages manual indexing, and retrieves relevant excerpts. |
| `src/models/model_client.py` | Communicates with Ollama and translates model-client failures into application exceptions. |
| `src/schemas/responses.py` | Defines Pydantic request and response structures. |

Pydantic validates data structures, not the factual accuracy of generated answers.

## Manual processing and storage

```text
PDF + Manufacturer + Model + Device Type
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
Attempt to move PDF to Processed manuals
  ↓
Refresh UI dropdowns
```

Each chunk stores:

- Extracted text
- Manual filename
- Manufacturer
- Equipment model
- Device type
- Start and end page numbers

Chroma data is stored under `data/chroma` and remains available after the application restarts. Moving a PDF does not remove its indexed content.

## Models

### Response model

The user can select from the Ollama models installed on the local machine. Tested models include `qwen3.5:2b`, `qwen3.5:4b`, and `qwen3.5:9b`.

Local inference avoids dependence on an external LLM API. Model selection allows users to compare response speed and quality on their hardware. The 9B model can respond slowly when running partly on the CPU.

### Embedding model

`BAAI/bge-m3` generates embeddings for both manual chunks and search queries. It is independent of the response-model dropdown.

The initial embedding model, `sentence-transformers/all-MiniLM-L6-v2`, had an input limit that was too short for the tested chunks. BGE-M3 accommodated their length.

## Additional AI capability: RAG

RAG is implemented and used to retrieve information from indexed manuals.

Search results are filtered by manufacturer and equipment model. The retrieved excerpts are included in the prompt, together with instructions to use only the supplied evidence and to acknowledge missing information.

Grounding reduces unsupported answers but does not guarantee correctness. Conversation history provides context and should not be treated as verified technical evidence.

## Setup

### Requirements

- Conda
- Ollama installed and running locally
- At least one installed Ollama response model
- PDF manuals to process

### Prepare the Python environment

From the repository root, create the environment using the supplied definition:

```powershell
conda env create -f environment.yml
```

Activate the environment using the name specified in `environment.yml`. The development environment used by the team is named `dev-ai`:

```powershell
conda activate dev-ai
```

If the environment already exists, activate it instead of creating it again.

### Prepare Ollama

Install a model suitable for the available hardware, for example:

```powershell
ollama pull qwen3.5:9b
```

Check installed models:

```powershell
ollama list
```

Ollama must be available at the configured address, normally `http://localhost:11434`.

### Start the application

Place manuals in `data/Manuals`, then run from the repository root:

```powershell
python -m app.main
```

Open the local URL printed in the terminal.

The embedding model may require an internet download on first use. Subsequent runs can load its cached files from disk. Processing a new manual still requires embedding computation.

Fresh installation with an empty or missing Chroma collection should be verified separately; the current setup has primarily been tested with an existing development database.

## Testing and evaluation

Automated tests verify application logic using test doubles for model responses, embeddings, and database operations. They do not measure live model accuracy or real retrieval quality.

Run the test suites from the repository root:

```powershell
python -m pytest tests/test_ai_service.py tests/test_knowledge.py tests/test_model_history.py -v
```

If pytest is missing from the active environment:

```powershell
python -m pip install pytest
```

If the default pytest temporary directory produces a permission error, use a dedicated test directory:

```powershell
python -m pytest tests/test_ai_service.py tests/test_knowledge.py tests/test_model_history.py -v --basetemp="$env:TEMP\manual-assistant-tests"
```

The `--basetemp` directory is disposable: pytest may clear its contents. Do not store manuals or other important files there.

### Latest automated results

On **2026-10-21**, separate test runs reported:

| Test suite | Passed | Failed | Skipped |
| :--- | :---: | :---: | :---: |
| AI service | 14 | 0 | 1 |
| Manual ingestion and retrieval | 9 | 0 | 0 |
| Model-client history handling | 1 | 0 | 0 |
| **Total** | **24** | **0** | **1** |

The dropdown integration placeholder remains skipped. The unsupported-device test also needs review to ensure it tests an explicit unknown selection rather than missing equipment.

See [evaluation results](evaluation/evaluation_results.md), [manual RAG checks](evaluation/manual_rag_checks.md), and [test instructions](tests/README.md).

### Live answer-quality observation

In a separate test with `qwen3.5:9b`, retrieval found the Rittal manual row defining A20 as “Voltage drop.” The model cited the correct excerpt but incorrectly claimed that the code had no defined meaning.

This case shows that correct retrieval and a source citation do not guarantee a correct interpretation. It is not included in the automated test totals.

## Known limitations

- PDF processing extracts text but does not interpret diagrams or images.
- Extracted tables may lose their layout, and the model may misinterpret them even when the required information is present.
- Source references and generated answers must be checked against the original manuals.
- The service passed a test confirming that retrieval uses the latest question. This does not establish that the UI maintains a complete multi-turn conversation history.
- Stored manual metadata cannot yet be edited through the UI. A misspelled manufacturer or model remains in the equipment list.
- Indexed manuals cannot yet be deleted through the UI. Moving or deleting a PDF does not delete its Chroma records.
- The duplicate-filename check occurs after indexing, so it does not prevent repeated embedding computation.
- Automatic folder creation, file movement, filename conflicts, and dropdown refreshes do not yet have dedicated automated assertions.
- Large response models and embedding computation can be slow on limited hardware.

## Future improvements

- Add UI actions for correcting manual metadata and deleting indexed manuals.
- Add automated tests for the complete manual-processing and dropdown-update workflow.
- Improve extraction and interpretation of tables and diagrams.
- Evaluate retrieval relevance and answer accuracy using documented questions and verified source passages.
- Improve handling of exact fault-code searches.
- Verify fresh installation and startup with no indexed manuals.
- Consider moving RAG functionality from `app/knowledge.py` to `src/capabilities/rag.py`, updating imports and storage paths accordingly.
