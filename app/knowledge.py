from pathlib import Path
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
import shutil

from functools import lru_cache

@lru_cache(maxsize=1)
def get_search_resources():
    embedding_model = SentenceTransformer("BAAI/bge-m3")

    chroma_client = chromadb.PersistentClient(
        path=str(Path(__file__).resolve().parent.parent / "data" / "chroma")
    )

    collection = chroma_client.get_collection(
        name="maintenance_manuals_bge_m3"
    )

    return embedding_model, collection

def get_equipment_pairs():
    """Return unique manufacturer and model pairs stored in ChromaDB."""
    _, collection = get_search_resources()
    stored = collection.get(include=["metadatas"])

    equipment_pairs = {
        (metadata["manufacturer"], metadata["model"])
        for metadata in stored["metadatas"]
        if metadata.get("manufacturer") and metadata.get("model")
    }

    return sorted(equipment_pairs)


def chunk_and_embed_pdf(pdf_path, manufacturer: str, model: str, device_type: str):
    
    #EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL = "BAAI/bge-m3"

    #pdf_path = Path(r"C:\Users\OMISTAJA\OneDrive - Hämeen ammattikorkeakoulu\HAMK\AI ja neural\Git_AI_Dev_Project\data\Manuals\VACON-100-Wall-mounted-Drives-Operating-Guide-DPD01711H-EN.pdf") # change the path if you want to test!
    pdf_path = Path(pdf_path)
    
    #Error handling for invalid file format or missing file
    if pdf_path.suffix.lower() != ".pdf":
        print("Invalid file format. Please provide a PDF file.")
        return 0, False
    
    if not pdf_path.is_file():
        print("File not found. Please check the file path.")
        return 0, False

    #Error handling for empty or scanned PDF
    try:
        reader = PdfReader(pdf_path)
    
        documents = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                documents.append({
                    "text": text.strip(),
                    "page": page_number
                })
            
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 0, False
        
        
    manual_text = ""
    page_ranges = []

    if documents:
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
    else:
        print("No readable text found. The PDF may be scanned.")
        return 0, False
        
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
                "Values need to satisfy: 0 <= overlap < chunk_size <= max_size."
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
                # search for the next paragraph break after the target end
                paragraph_end = manual_text.find(
                    "\n\n", target_end, limit_end
                )

                if paragraph_end != -1:
                    end = paragraph_end + 2
                else:
                    # If no paragraph break is found, use the limit end
                    end = limit_end

            chunk_text = manual_text[start:end]

            # Page ranges for the current chunk
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
        "manufacturer": manufacturer,
        "model": model,
        "device_type": device_type,
    }
    
    CHUNKS = make_chunks(
        manual_text,
        page_ranges,
        manual_metadata,
    ) 
    

    embedding_model = SentenceTransformer(EMBEDDING_MODEL)


    chunk_vectors = embedding_model.encode(
        [chunk["text"] for chunk in CHUNKS],
        normalize_embeddings=True,
    ).tolist()

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

   
    #Move the processed PDF to the "Processed manuals" directory
    sourcePath = Path(pdf_path)
    processedPath  = Path("data/Processed manuals") / sourcePath.name
    processedPath.parent.mkdir(parents=True, exist_ok=True)
    #If already exists, do not overwrite, just print a message
    if not processedPath.exists():
        shutil.move(sourcePath, processedPath)
    else:
        print(f"File already exists in the 'Processed manuals' directory: {sourcePath.name}. Not moving the file.")
    
    
    return len(CHUNKS), True

def retrieve(
    question: str, 
    manufacturer: str, 
    model: str,
    embedding_model,
    collection, 
    top_k=3
    ):
    if collection.count() == 0:
        return []
    
    query_vector = embedding_model.encode(
        [question],
        normalize_embeddings=True,
    ).tolist()[0]

    result = collection.query(
        query_embeddings=[query_vector],
        n_results=min(top_k, collection.count()),
        where={
            "$and": [
                {"manufacturer": manufacturer},
                {"model": model}
            ]
            },
        include=["documents", "metadatas", "distances"],
    )

    evidence = []

    for chunk_id, text, metadata, distance in zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        evidence.append({
            "id": chunk_id,
            "text": text,
            "manual": metadata["manual"],
            "page_start": metadata["page_start"],
            "page_end": metadata["page_end"],
            "distance": round(float(distance), 3),
        })

    return evidence
