"""Retrieval and ingestion tests never write to the real Chroma database."""
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from app import knowledge

@pytest.fixture
def ingest(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    pdf = tmp_path / "manual.pdf"
    pdf.write_bytes(b"test fixture")
    reader = MagicMock()
    encoder = MagicMock()
    encoder.encode.return_value.tolist.return_value = [[0.1, 0.2]]
    factory = MagicMock(return_value=encoder)
    db = MagicMock()
    monkeypatch.setattr(knowledge, "PdfReader", reader)
    monkeypatch.setattr(knowledge, "SentenceTransformer", factory)
    monkeypatch.setattr(knowledge.chromadb, "PersistentClient", MagicMock(return_value=db))
    return SimpleNamespace(pdf=pdf, reader=reader, encoder=encoder, factory=factory,
                           collection=db.get_or_create_collection.return_value)

@pytest.mark.parametrize("kind", ["wrong_extension", "missing", "corrupt", "no_text"])
def test_invalid_pdf(ingest, kind):
    path = ingest.pdf
    if kind == "wrong_extension":
        path = path.with_suffix(".txt")
        path.write_text("not PDF")
    elif kind == "missing":
        path = path.parent / "missing.pdf"
    elif kind == "corrupt":
        ingest.reader.side_effect = ValueError("broken PDF")
    else:
        ingest.reader.return_value.pages = [
            SimpleNamespace(extract_text=lambda: None),
            SimpleNamespace(extract_text=lambda: "   ")]
    assert knowledge.chunk_and_embed_pdf(path, "Vacon", "100", "Drive") == (0, False)
    ingest.factory.assert_not_called()
    ingest.collection.upsert.assert_not_called()

def test_real_corrupt_pdf_is_rejected(tmp_path, monkeypatch):
    pdf = tmp_path / "broken.pdf"
    pdf.write_bytes(b"this is not a PDF")
    factory = MagicMock()
    monkeypatch.setattr(knowledge, "SentenceTransformer", factory)
    assert knowledge.chunk_and_embed_pdf(pdf, "Vacon", "100", "Drive") == (0, False)
    factory.assert_not_called()

def test_chunk_metadata_preserves_original_page_numbers(ingest):
    # One chunk spans pages 1 and 3, with a blank page between them.
    ingest.reader.return_value.pages = [
        SimpleNamespace(extract_text=lambda: "FIRST PAGE"),
        SimpleNamespace(extract_text=lambda: ""),
        SimpleNamespace(extract_text=lambda: "THIRD PAGE")]
    assert knowledge.chunk_and_embed_pdf(ingest.pdf, "Vacon", "100", "Drive") == (1, True)
    ingest.collection.upsert.assert_called_once()
    saved = ingest.collection.upsert.call_args.kwargs
    assert saved["documents"] == ["FIRST PAGE\nTHIRD PAGE"]
    assert saved["metadatas"] == [{
        "manual": "manual.pdf", "manufacturer": "Vacon", "model": "100",
        "device_type": "Drive", "page_start": 1, "page_end": 3}]
    assert len(saved["ids"]) == len(set(saved["ids"])) == 1

def test_retrieval_filter_and_source_metadata():
    encoder, collection = MagicMock(), MagicMock()
    encoder.encode.return_value.tolist.return_value = [[0.1, 0.2]]
    collection.count.return_value = 2
    collection.query.return_value = {
        "ids": [["chunk-1"]], "documents": [["source text"]],
        "metadatas": [[{"manual": "manual.pdf", "page_start": 4, "page_end": 5}]],
        "distances": [[0.12345]]}
    result = knowledge.retrieve("question", "Siemens", "G120", encoder, collection)
    encoder.encode.assert_called_once_with(["question"], normalize_embeddings=True)
    assert collection.query.call_args.kwargs["where"] == {
        "$and": [{"manufacturer": "Siemens"}, {"model": "G120"}]}
    assert result == [{"id": "chunk-1", "text": "source text", "manual": "manual.pdf",
                       "page_start": 4, "page_end": 5, "distance": 0.123}]

def test_no_matching_documents():
    encoder, collection = MagicMock(), MagicMock()
    encoder.encode.return_value.tolist.return_value = [[0.1]]
    collection.count.return_value = 2
    collection.query.return_value = {k: [[]] for k in
        ("ids", "documents", "metadatas", "distances")}
    assert knowledge.retrieve("question", "Unknown", "X", encoder, collection) == []


def test_empty_collection_returns_without_query():
    encoder, collection = MagicMock(), MagicMock()
    encoder.encode.return_value.tolist.return_value = [[0.1]]
    collection.count.return_value = 0
    result = knowledge.retrieve("question", "Vacon", "100", encoder, collection)
    collection.query.assert_not_called()
    assert result == []
