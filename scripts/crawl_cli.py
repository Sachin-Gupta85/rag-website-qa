"""Crawl a site from the command line.

Usage:
    python scripts/crawl_cli.py https://example.com [max_pages]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest import ingest_site  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print("Usage: python scripts/crawl_cli.py <url> [max_pages]")
        return 1
    url = argv[0]
    max_pages = int(argv[1]) if len(argv) > 1 else None
    print(f"Crawling {url} …")
    n = ingest_site(url, max_pages=max_pages)
    print(f"Indexed {n} chunks. Start the API with: uvicorn main:app --reload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
