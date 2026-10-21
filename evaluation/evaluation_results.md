# Evaluation Results Summary

## Summary Overview

- **Date of Evaluation:** 2026-10-21
- **Components Evaluated:** AI service, manual ingestion and retrieval, and model-client message construction.
- **Model Evaluated:** No live language model. Model responses, embeddings, and database operations were replaced with test doubles.
- **Test Cases Collected:** 25
- **Total Test Cases Executed:** 24
- **Passed:** 24
- **Failed:** 0
- **Skipped:** 1
- **Pass Rate:** 100% of executed tests

Results were collected from separate test runs.

## Performance by Category

| Test Suite | Executed Cases | Passed | Failed | Skipped |
| :--- | :---: | :---: | :---: | :---: |
| AI Service | 14 | 14 | 0 | 1 |
| Manual Ingestion and Retrieval | 9 | 9 | 0 | 0 |
| Model-Client History Handling | 1 | 1 | 0 | 0 |
| **Total** | **24** | **24** | **0** | **1** |

## Key Findings & Failure Analysis

### What worked well

- Questions and equipment details were passed correctly to retrieval.
- Retrieved excerpts, source metadata, conversation history, grounding instructions, and model selection were forwarded correctly.
- Retrieval used the latest question in the follow-up test.
- Empty input and missing equipment were rejected.
- Empty retrieval results prevented a model call.
- Simulated retrieval and model-client failures produced controlled responses.
- Invalid file extensions, missing files, corrupted PDFs, and PDFs without readable text were handled.
- Chunk metadata preserved original page numbers, including when blank pages were skipped.
- Retrieval applied manufacturer and model filters and returned source metadata.
- Empty collections returned an empty result without querying Chroma.
- Model-client messages preserved conversation order without modifying the original history.

### Issues resolved during testing

Several service tests still used the previous text-based equipment input. They were updated to pass the equipment selection separately.

A temporary-directory permission issue prevented PDF tests from starting. The tests were rerun using a dedicated temporary directory. The ingestion fixture also changes the working directory to isolate relative file operations from the project.

The empty-collection test identified a missing guard in retrieval. A check was added to return an empty list before embedding generation or database queries when the collection contains no chunks.

### Remaining test limitations

- The dropdown integration test is still skipped. The dropdown exists, but this placeholder does not verify its operation.
- The unsupported-device test needs review: its original implementation omitted the equipment argument and may only verify missing equipment.
- File movement, automatic destination-folder creation, filename conflicts, and dropdown refreshes do not yet have dedicated automated assertions.
- These tests do not measure real retrieval relevance, language-model accuracy, or inference performance.

### Observed failure in a separate live model test

During a previous test with `qwen3.5:9b`, the retrieved Rittal manual excerpt contained:

> A20 Voltage drop Error display not shown Event is stored in the log file

The model nevertheless stated that A20 had no defined meaning, despite citing the correct excerpt and page.

Retrieval found the relevant information, but the model misinterpreted the extracted table. This demonstrates that a source citation alone does not guarantee a correct answer. This observation is separate from the automated test counts above.

## Action Items & Improvements

- [ ] Update the unsupported-device test to supply an explicit unknown equipment selection.
- [ ] Replace the skipped dropdown placeholder with an actual integration test.
- [ ] Add tests for automatic folder creation, processed-file movement, and filename conflicts.
- [ ] Verify that both dropdown menus refresh after successful processing.
- [ ] Evaluate retrieval and generated answers against known passages in the original manuals.
- [ ] Investigate incorrect interpretation of tables extracted from PDFs.
- [ ] Add functionality for correcting stored manual metadata and deleting indexed manuals.
