"""Crawl a site, chunk pages, embed, and persist a Chroma vector store."""
from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import VECTOR_STORE_DIR, settings
from .crawler import crawl


def _embeddings() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(model_name=settings.embedding_model)


def ingest_site(seed_url: str, max_pages: int | None = None) -> int:
    """Crawl *seed_url* and build a persistent vector store. Returns #chunks."""
    pages = crawl(seed_url, max_pages=max_pages)
    if not pages:
        raise RuntimeError(f"No crawlable HTML pages found at {seed_url}")

    docs = [
        Document(page_content=p.text, metadata={"source": p.url, "title": p.title})
        for p in pages
        if p.text.strip()
    ]
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        add_start_index=True,
    )
    chunks = splitter.split_documents(docs)

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    Chroma.from_documents(
        documents=chunks,
        embedding=_embeddings(),
        collection_name=settings.collection_name,
        persist_directory=str(VECTOR_STORE_DIR),
    )
    return len(chunks)


def load_vector_store() -> Chroma:
    if not VECTOR_STORE_DIR.exists():
        raise RuntimeError("No vector store yet. Crawl a site first (POST /ingest).")
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=_embeddings(),
        persist_directory=str(VECTOR_STORE_DIR),
    )
