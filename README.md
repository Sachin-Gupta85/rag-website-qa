# 🔎 rag-website-qa

> Crawl any website, then ask questions answered **only from that site's pages** — every answer links back to the source URLs.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688)
![LangChain](https://img.shields.io/badge/LangChain-0.3-green)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow)

A **Retrieval-Augmented Generation** service exposed over a clean **FastAPI** backend
with a tiny built-in web UI. Point it at a URL, it politely crawls the same domain,
builds a local vector index, and answers questions grounded in what it found — with
citations.

---

## ✨ Features

- **Same-domain crawler** — breadth-first, HTML-only, polite rate limiting, strips nav/boilerplate.
- **Grounded, cited answers** — responses link the exact pages used; refuses when the site doesn't cover it.
- **FastAPI + OpenAPI docs** — `/ingest`, `/ask`, `/health`, interactive docs at `/docs`.
- **Built-in minimal UI** — no framework; served at `/`.
- **Local embeddings** — `sentence-transformers`, no embedding API cost.
- **Any OpenAI-compatible LLM** — OpenAI, Groq, Together, or local Ollama.

## 🏗️ Architecture

```
  URL ─▶ Crawler (same-domain, BFS) ─▶ clean text
                                           │ chunk + local embeddings
                                           ▼
                                     Chroma vector store
                                           │ top-k retrieval
   Question ─▶ /ask ─▶ retrieve ─▶ context-only prompt ─▶ LLM ─▶ answer + source URLs
```

## 🚀 Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add OPENAI_API_KEY (or Ollama block)

uvicorn main:app --reload       # UI: http://localhost:8000  ·  Docs: /docs
```

In the UI: **paste a URL → Crawl → ask a question.**

### API usage

```bash
# 1. Crawl a site
curl -X POST localhost:8000/ingest \
  -H 'content-type: application/json' \
  -d '{"url": "https://example.com", "max_pages": 20}'

# 2. Ask
curl -X POST localhost:8000/ask \
  -H 'content-type: application/json' \
  -d '{"question": "What does this site offer?"}'
```

Or crawl from the terminal: `python scripts/crawl_cli.py https://example.com 20`

## ⚙️ Configuration (`.env`)

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` / `OPENAI_BASE_URL` | — | LLM endpoint (swap base URL for Ollama) |
| `LLM_MODEL` | `gpt-4o-mini` | Chat model |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local embeddings |
| `MAX_PAGES` | `40` | Crawl budget |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` / `TOP_K` | `1000` / `150` / `4` | Retrieval tuning |

## 🗂️ Layout

```
rag-website-qa/
├── main.py              # FastAPI app (/ingest, /ask) + serves the UI
├── src/
│   ├── crawler.py       # polite same-domain BFS crawler
│   ├── ingest.py        # crawl → chunk → embed → Chroma
│   ├── rag.py           # retrieve → prompt → cited answer
│   └── config.py
├── static/index.html    # minimal built-in UI
├── scripts/crawl_cli.py
└── requirements.txt
```

## ⚠️ Be a good citizen

Crawl only sites you're allowed to, respect `robots.txt` and rate limits, and keep
`MAX_PAGES` modest. This tool is for documentation, your own sites, and research.

## 📝 License

MIT — see [LICENSE](LICENSE).
