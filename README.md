# AI Maintenance Manual Assistant for Industrial Equipment

## Team members

- Budhathoki Tika (tika.budhathoki@student.hamk.fi)
- Tusher Monjurul (monjurul.tusher@student.hamk.fi)
- Amil Mahfuj (mahfuj.amil@student.hamk.fi)
- Petri Suopanki (petri.suopanki@student.hamk.fi )

## Problem

### Intended users
The primary users are industrial maintenance personnel and equipment operators who need instructions related to equipment fault codes.

### Problem statement
Finding troubleshooting instructions in lengthy, equipment-specific manuals takes time. Paper manuals for older equipment may also be missing or unavailable. The application helps users find instructions for the correct equipment and fault code in stored digital manuals and presents them as clear steps.

### Why AI is appropriate
Traditional search can locate a fault code, but an LLM enables natural-language queries, clarifying questions, and the combination of information from different manual sections into an understandable response. Retrieval-Augmented Generation (RAG) grounds the response in the content of the selected manuals.

## Solution
We will develop an AI assistant that retrieves troubleshooting and repair instructions from stored operation and maintenance manuals. It presents numbered steps, source references, and the safety requirements stated in the manual.
The prototype will use approximately 2–5 example manuals, a Gradio user interface, and an LLM running locally through Ollama. Automated web search is outside the scope of the first version.
The application will be evaluated using demonstration questions to assess answer accuracy, source references, and the handling of missing information.

## Main user workflow

1. **User Input:** The user enters a fault code and equipment details through the Gradio interface.
2. **Processing & Guardrails:** The service layer validates the input, requests additional details when needed, and retrieves relevant sections from the correct manual. The response is restricted to the retrieved information.
3. **Model Response:** The LLM running through Ollama turns the retrieved instructions into a numbered list of steps, displayed in the interface with source references. If insufficient information is found, the application explains this and advises the user to look for the correct manual on the manufacturer’s website.

## Architecture

Below is the initial starter architecture. As your project evolves with additional capabilities, replace or extend this diagram in [`docs/architecture.md`](docs/architecture.md).

```text
User
  ↓
Gradio UI (app/ui.py)
  ↓
Application / AI Service (src/services/ai_service.py)
  ↓
Model Client (src/models/model_client.py)
  ↓
Ollama (Local LLM Server)
```

> **Core Architectural Rule:** The user interface must NEVER communicate directly with the model client or Ollama. All interactions must pass through the service layer (`ai_service.py`).

## Model

- **Model used:** e.g., `llama3.2` (or specified local Ollama model)
- **Selection rationale:** Why was this specific model chosen for your project (e.g., lightweight, performance, context size)?

## Additional AI capability

RAG (Retrieval-Augmented Generation)

### Capability justification
Explain why the selected capability is useful and necessary for your application's user problem.

## Setup

### 1. Create the Conda environment

```bash
conda env create -f environment.yml
```

### 2. Activate the environment

```bash
conda activate dev-ai-project
```

### 3. Configure environment variables

Copy `.env.example` to create your local `.env` configuration file:

On Linux / macOS:
```bash
cp .env.example .env
```

On Windows (Command Prompt / PowerShell):
```powershell
copy .env.example .env
```

Ensure `.env` contains valid values for `OLLAMA_BASE_URL` and `MODEL_NAME`:
```env
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=llama3.2
```

### 4. Start Ollama

Make sure Ollama is installed and running locally, then pull your configured model:

```bash
ollama run llama3.2
```

### 5. Run the application

Run the application from the root directory of the project:

```bash
python -m app.main
```

Then open your browser at `http://localhost:7860`.

### 6. Run automated tests

```bash
pytest
```

## Evaluation

Describe your evaluation methodology and summarize key results. Starter test cases can be found in [`evaluation/test_cases.json`](evaluation/test_cases.json).

Refer to [`evaluation/README.md`](evaluation/README.md) for guidelines on defining success, edge cases, and failure scenarios.

## Known limitations

- Highlight known system limitations, unhandled edge cases, or boundaries of current capabilities.

## Future improvements

- List planned feature enhancements, architectural refactorings, or future capabilities.
