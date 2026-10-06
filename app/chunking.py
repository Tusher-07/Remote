from pathlib import Path
from pypdf import PdfReader

pdf_path = Path(r"C:\Users\OMISTAJA\OneDrive - Hämeen ammattikorkeakoulu\HAMK\AI ja neural\Git_AI_Dev_Project\data\Manuals\VACON-100-Wall-mounted-Drives-Operating-Guide-DPD01711H-EN.pdf") # change the path if you want to test!
reader = PdfReader(pdf_path)

documents = []

for page_number, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""

    if text.strip():
        documents.append({
            "text": text.strip(),
            "manual": pdf_path.name,
            "manufacturer": "Vacon",
            "model": "100",
            "device_type": "Frequency converter",
            "page": page_number
        })

def make_chunks(documents, chunk_size=2000, overlap=200):
    if not 0 <= overlap < chunk_size:
        raise ValueError("Overlapping needs to be 0–(chunk_size − 1).")

    chunks = []

    for document_number, document in enumerate(documents, start=1):
        text = document["text"]
        start = 0
        number = 1

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]

            if chunk_text.strip():
                chunks.append({
                    "id": f'doc{document_number}-p{document["page"]}-c{number}',
                    "text": chunk_text.strip(),
                        "metadata": {
                            "manual": document["manual"],
                            "manufacturer": document["manufacturer"],
                            "model": document["model"],
                            "device_type": document["device_type"],
                            "page": document["page"],
                        },
                })

            if end >= len(text):
                break

            start = end - overlap
            number += 1

    return chunks

CHUNKS = make_chunks(documents, chunk_size=2000, overlap=200)

#test print
print("Pages with text:", len(documents))
print("Chunks:", len(CHUNKS))

if CHUNKS:
    print(CHUNKS[0])