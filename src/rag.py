"""RAG chain that answers questions grounded in crawled web pages, with URL citations."""
from __future__ import annotations

from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .config import settings

SYSTEM_PROMPT = """You answer questions using ONLY the provided context, which was \
crawled from a website.

- Use only facts present in the context. If the answer is not there, say \
"I couldn't find that on the site." Never invent details.
- Be concise.
- After the answer, list the source URLs you used.
"""

PROMPT = ChatPromptTemplate.from_messages(
    [("system", SYSTEM_PROMPT), ("human", "Question:\n{question}\n\nContext:\n{context}")]
)


@dataclass
class Source:
    url: str
    title: str


@dataclass
class RagAnswer:
    answer: str
    sources: list[Source]


def _format_context(docs: list[Document]) -> str:
    return "\n\n---\n\n".join(
        f"[{d.metadata.get('title', '')} — {d.metadata.get('source', '')}]\n{d.page_content}"
        for d in docs
    )


def _llm() -> ChatOpenAI:
    settings.validate_llm()
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        temperature=0.0,
    )


def answer_question(store: Chroma, question: str) -> RagAnswer:
    docs = store.as_retriever(search_kwargs={"k": settings.top_k}).invoke(question)
    if not docs:
        return RagAnswer("I couldn't find anything relevant on the site.", [])

    answer = (PROMPT | _llm() | StrOutputParser()).invoke(
        {"question": question, "context": _format_context(docs)}
    )
    # De-duplicate sources by URL, preserving order.
    seen, sources = set(), []
    for d in docs:
        url = d.metadata.get("source", "")
        if url and url not in seen:
            seen.add(url)
            sources.append(Source(url=url, title=d.metadata.get("title", url)))
    return RagAnswer(answer=answer, sources=sources)
