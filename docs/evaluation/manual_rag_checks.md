# Manual RAG evaluation

These checks require the actual Vacon 100 manual and a running model.
They have NOT been executed by the unit tests. Record the model, date,
question, retrieved filenames/pages/text, full answer, and pass/fail reasoning.

1. Ask how to isolate digital inputs from ground.
   Reference: VACON 100 Wall-mounted Drives Operating Guide, section 7.3.2.
   Check the original page and diagram: DIP switch; FLOAT is floating,
   GND is connected to ground. Verify the retrieved text supports every claim.
   If diagram labels are missing from extracted text, record this limitation.
2. Ask which digital input terminals section 7.3.2 describes.
   Reference: the supplied section specifies terminals 8–10 and 14–16.
   Verify retrieval finds that section and the answer cites the correct source.
3. Ask for the cafeteria opening hours.
   Expected: no supported answer from the equipment manual, no invented hours.
4. Ask a follow-up after a supported answer.
   Expected: retrieval uses the new question and retains the chosen device.
   Currently known incomplete.
5. Select a second device once its manual and dropdown are available.
   Expected: all retrieved chunks match the selected manufacturer/model;
   no Vacon answer for another device.

For each answer, separately assess retrieval correctness, factual support,
source/page correctness, and whether unsupported details were invented.
Model output alone is not evidence of correctness.
