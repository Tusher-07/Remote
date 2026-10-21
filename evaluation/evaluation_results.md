# Evaluation Results Summary

## Summary Overview

- **Date of Evaluation:** 2026-10-21
- **Component Evaluated:** Application AI service (`src/services/ai_service.py`)
- **Model Evaluated:** No live language model; model responses and retrieval results were mocked.
- **Test Cases Collected:** 15
- **Total Test Cases Executed:** 14
- **Passed:** 14
- **Failed:** 0
- **Skipped:** 1
- **Pass Rate:** 100% of executed tests
- **Execution Time:** 22.21 seconds

## Performance by Category

| Category | Executed Cases | Passed | Failed | Pass Rate |
| :--- | :---: | :---: | :---: | :---: |
| Configuration | 1 | 1 | 0 | 100% |
| Successful Request Processing | 2 | 2 | 0 | 100% |
| Follow-up Query Handling | 1 | 1 | 0 | 100% |
| Validation and Failure / Edge Cases | 10 | 10 | 0 | 100% |

The dropdown integration test was skipped and is excluded from the pass rate.

## Key Findings & Failure Analysis

### What worked well

- Equipment details and the question were passed correctly to retrieval.
- Retrieved evidence and source metadata were included in the model prompt.
- Conversation history, model selection, and grounding instructions were forwarded correctly.
- Retrieval used the latest question in the follow-up test.
- Empty input and missing equipment were rejected before retrieval or inference.
- Empty retrieval results prevented a model call.
- Simulated retrieval failures, Ollama connection errors, missing models, and general model-client errors produced controlled responses.

### Evaluation limitations

These tests verify application logic using test doubles. They do not measure actual retrieval relevance, model accuracy, inference speed, or PDF processing.

The unsupported-device test needs review: its original implementation omitted the equipment argument, so it may verify missing equipment rather than rejection of an unknown device.

The skipped dropdown test still contains an outdated placeholder. The dropdown now exists, but its integration has not been verified by this test.

### Observed model failure in a separate manual check

In a previous live test, the model incorrectly stated that fault code A20 had no defined meaning, although the retrieved excerpt included “A20 Voltage drop.” The model cited the relevant excerpt but misinterpreted its contents.

This demonstrates that correct retrieval and source citations do not guarantee a factually correct answer. This manual observation is not included in the automated test counts above.

## Action Items & Improvements

- [ ] Update the unsupported-device test to supply an explicit unknown equipment selection.
- [ ] Replace the skipped dropdown placeholder with an actual integration test.
- [ ] Resolve the temporary-directory permission issue and rerun the PDF-processing tests.
- [ ] Test automatic folder creation, processed-file movement, and filename conflicts.
- [ ] Verify that both dropdown menus refresh after successful processing.
- [ ] Evaluate real retrieval and answer quality against known manual passages.
- [ ] Investigate incorrect interpretation of extracted PDF tables.
