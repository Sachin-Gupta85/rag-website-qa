"""FastAPI app: crawl a site, then ask questions over it with cited answers.

Run with:  uvicorn main:app --reload
Docs at:   http://localhost:8000/docs
UI at:     http://localhost:8000/
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.ingest import ingest_site, load_vector_store
from src.rag import answer_question

app = FastAPI(title="rag-website-qa", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"


class IngestRequest(BaseModel):
    url: str = Field(..., examples=["https://example.com"])
    max_pages: int | None = Field(None, ge=1, le=200)


class AskRequest(BaseModel):
    question: str = Field(..., examples=["What does this site offer?"])


@app.post("/ingest")
def ingest(req: IngestRequest):
    try:
        n_chunks = ingest_site(req.url, max_pages=req.max_pages)
    except Exception as exc:  # surfaced to the client as a clean 400
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "indexed", "chunks": n_chunks, "seed": req.url}


@app.post("/ask")
def ask(req: AskRequest):
    try:
        store = load_vector_store()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result = answer_question(store, req.question)
    return {
        "answer": result.answer,
        "sources": [{"url": s.url, "title": s.title} for s in result.sources],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve a tiny single-page UI at "/".
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index():
        return FileResponse(STATIC_DIR / "index.html")
