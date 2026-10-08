"""Ingestion: parse file -> chunk -> embed -> store in vector DB."""
import os
from docx import Document as DocxFile
from langchain_core.documents import Document as LCDoc
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from .rag import get_vectorstore

ALLOWED = {".pdf", ".docx", ".txt"}


def extract_pages(path):
    """Return a list of (page_number, text). DOCX/TXT are grouped into pseudo-pages."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        reader = PdfReader(path)
        return [(i + 1, p.extract_text() or "") for i, p in enumerate(reader.pages)]
    if ext == ".docx":
        text = "\n".join(p.text for p in DocxFile(path).paragraphs if p.text.strip())
    else:
        with open(path, encoding="utf-8", errors="ignore") as f:
            text = f.read()
    size = 3000
    return [(i // size + 1, text[i:i + size]) for i in range(0, len(text), size)]


def ingest_document(doc):
    pages = extract_pages(doc.path)
    if not any(t.strip() for _, t in pages):
        raise ValueError("No extractable text (scanned PDFs need OCR).")

    # Splits on paragraph/line breaks first, so clauses tend to stay together.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = []
    for page_no, text in pages:
        for piece in splitter.split_text(text):
            chunks.append(LCDoc(page_content=piece,
                                metadata={"doc_id": doc.id, "page": page_no}))
    get_vectorstore().add_documents(chunks)
    doc.page_count = len(pages)
    return len(chunks)


def delete_vectors(doc_id):
    get_vectorstore().delete(where={"doc_id": doc_id})
