"""A small, polite same-domain web crawler that yields clean page text."""
from __future__ import annotations

import time
from dataclasses import dataclass
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import settings

HEADERS = {"User-Agent": "rag-website-qa/0.1 (+https://github.com/)"}


@dataclass
class Page:
    url: str
    title: str
    text: str


def _clean_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def _same_domain(seed: str, url: str) -> bool:
    return urlparse(seed).netloc == urlparse(url).netloc


def crawl(seed_url: str, max_pages: int | None = None) -> list[Page]:
    """Breadth-first crawl within the seed's domain, up to max_pages."""
    max_pages = max_pages or settings.max_pages
    seen: set[str] = set()
    queue: list[str] = [urldefrag(seed_url)[0]]
    pages: list[Page] = []

    while queue and len(pages) < max_pages:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            if "text/html" not in resp.headers.get("content-type", ""):
                continue
        except requests.RequestException:
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        title = (soup.title.string if soup.title else url) or url
        pages.append(Page(url=url, title=title.strip(), text=_clean_text(soup)))

        for a in soup.find_all("a", href=True):
            link = urldefrag(urljoin(url, a["href"]))[0]
            if link not in seen and _same_domain(seed_url, link):
                queue.append(link)

        time.sleep(0.3)  # be polite

    return pages
