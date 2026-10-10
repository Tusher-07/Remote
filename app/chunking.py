from pathlib import Path
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb

#EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_MODEL = "BAAI/bge-m3"

pdf_path = Path(r"C:\Users\OMISTAJA\OneDrive - Hämeen ammattikorkeakoulu\HAMK\AI ja neural\Git_AI_Dev_Project\data\Manuals\VACON-100-Wall-mounted-Drives-Operating-Guide-DPD01711H-EN.pdf") # change the path if you want to test!
reader = PdfReader(pdf_path)

documents = []

for page_number, page in enumerate(reader.pages, start=1):
    text = page.extract_text() or ""

    if text.strip():
        documents.append({
            "text": text.strip(),
            "page": page_number
        })
        
manual_text = ""
page_ranges = []

for document in documents:
    
    if manual_text:
        manual_text += "\n"

    start = len(manual_text)
    manual_text += document["text"]
    end = len(manual_text)

    page_ranges.append({
        "page": document["page"],
        "start": start,
        "end": end,
    })
    
def make_chunks(
    manual_text,
    page_ranges,
    metadata,
    chunk_size=1000,
    overlap=200,
    max_size=1500,
):
    if not 0 <= overlap < chunk_size <= max_size:
        raise ValueError(
            "Arvojen pitää täyttää: 0 <= overlap < chunk_size <= max_size."
        )

    chunks = []
    start = 0
    number = 1

    while start < len(manual_text):
        target_end = start + chunk_size
        limit_end = min(start + max_size, len(manual_text))

        if target_end >= len(manual_text):
            end = len(manual_text)
        else:
            # Etsitään tyhjä rivi tavoitekoon jälkeen.
            paragraph_end = manual_text.find(
                "\n\n", target_end, limit_end
            )

            if paragraph_end != -1:
                end = paragraph_end + 2
            else:
                # Jos kappalerajaa ei löydy, käytetään vararajaa.
                end = limit_end

        chunk_text = manual_text[start:end]

        # Sivut, joiden tekstiä osuu tähän chunkiin.
        pages = [
            page_range["page"]
            for page_range in page_ranges
            if page_range["start"] < end
            and page_range["end"] > start
        ]

        if chunk_text.strip() and pages:
            chunks.append({
                "id": f'{metadata["manual"]}-c{number}',
                "text": chunk_text.strip(),
                "metadata": {
                    **metadata,
                    "page_start": pages[0],
                    "page_end": pages[-1],
                },
            })

        if end >= len(manual_text):
            break

        start = end - overlap
        number += 1

    return chunks

manual_metadata = {
    "manual": pdf_path.name,
    "manufacturer": "Vacon",
    "model": "100",
    "device_type": "Frequency converter",
}
CHUNKS = make_chunks(
    manual_text,
    page_ranges,
    manual_metadata,
) 

embedding_model = SentenceTransformer(EMBEDDING_MODEL)


#token length testing


# token_lengths = [
#     len(embedding_model.tokenizer.encode(
#         chunk["text"],
#         truncation=False,
#         add_special_tokens=True,
#     ))
#     for chunk in CHUNKS
# ]

# limit = embedding_model.max_seq_length

# print("Mallin tokenraja:", limit)
# print("Pisin chunk tokeneina:", max(token_lengths, default=0))
# print(
#     "Rajan ylittäviä chunkkeja:",
#     sum(length > limit for length in token_lengths),
#     "/",
#     len(CHUNKS),
# )






chunk_vectors = embedding_model.encode(
    [chunk["text"] for chunk in CHUNKS],
    normalize_embeddings=True,
).tolist()

print(chunk_vectors[0])

chroma_client = chromadb.PersistentClient(
    path=str(Path(__file__).resolve().parent.parent / "data" / "chroma")
)

collection = chroma_client.get_or_create_collection(
    name="maintenance_manuals_bge_m3",
    metadata={"hnsw:space": "cosine"},
)

collection.upsert(
    ids=[chunk["id"] for chunk in CHUNKS],
    embeddings=chunk_vectors,
    documents=[chunk["text"] for chunk in CHUNKS],
    metadatas=[chunk["metadata"] for chunk in CHUNKS],
)

print("Indexed chunks:", collection.count())
print(type(collection))

#test prints
#print("Pages with text:", len(documents))
#print("Chunks:", len(CHUNKS))
#print("Manuaalin merkkejä:", len(manual_text))
#print("Ensimmäiset sivurajat:", page_ranges[:3])

#if CHUNKS:
#    print(CHUNKS[0])