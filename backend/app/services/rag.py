"""RAG chat, document analysis (summary + risky clauses) and comparison."""
import json
import os
from functools import lru_cache
from typing import List

from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

NOT_FOUND = "I couldn't find this in the document."


# ---------- model factories (swap providers via .env) ----------
@lru_cache(maxsize=1)
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "groq")
    model = os.getenv("LLM_MODEL")
    if provider in ("groq", "openrouter"):
        from langchain_openai import ChatOpenAI
        urls = {"groq": "https://api.groq.com/openai/v1", "openrouter": "https://openrouter.ai/api/v1"}
        keys = {"groq": "GROQ_API_KEY", "openrouter": "OPENROUTER_API_KEY"}
        return ChatOpenAI(model=model, temperature=0, base_url=urls[provider],
                          api_key=os.getenv(keys[provider]))
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model or "gemini-2.0-flash", temperature=0,
                                      google_api_key=os.getenv("GEMINI_API_KEY"))
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model or "claude-sonnet-4-5", temperature=0)
    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=model or "llama3.2", temperature=0)
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model=model or "gpt-4o-mini", temperature=0)


@lru_cache(maxsize=1)
def get_vectorstore():
    kind = os.getenv("EMBEDDINGS", "local")
    if kind == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001",
                                           google_api_key=os.getenv("GEMINI_API_KEY"))
    elif kind == "openai":
        from langchain_openai import OpenAIEmbeddings
        emb = OpenAIEmbeddings(model="text-embedding-3-small")
    else:
        from langchain_huggingface import HuggingFaceEmbeddings
        emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return Chroma(collection_name="legallens", embedding_function=emb,
                  persist_directory=os.getenv("CHROMA_DIR", "chroma_db"))


# ---------- chat ----------
REWRITE = ChatPromptTemplate.from_template(
    "Given the chat history and a follow-up question, rewrite the follow-up as a "
    "standalone question. Return only the question.\n\nHistory:\n{history}\n\n"
    "Follow-up: {question}")

ANSWER = ChatPromptTemplate.from_template(
    "You answer questions about a legal document using ONLY the excerpts below.\n"
    "Rules:\n- Cite pages like [Page 3] after each claim.\n"
    "- If the excerpts do not contain the answer, reply exactly: " + NOT_FOUND + "\n"
    "- Use plain language. You are not a lawyer; do not give legal advice.\n\n"
    "Excerpts:\n{context}\n\nQuestion: {question}\nAnswer:")


def answer_question(doc_id, question, history):
    """history: list of (role, content). Returns (answer, sources)."""
    llm = get_llm()
    standalone = question
    if history:
        text = "\n".join(f"{r}: {c}" for r, c in history[-6:])
        standalone = (REWRITE | llm | StrOutputParser()).invoke(
            {"history": text, "question": question})

    retriever = get_vectorstore().as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 20, "filter": {"doc_id": doc_id}})
    docs = retriever.invoke(standalone)
    if not docs:
        return NOT_FOUND, []

    context = "\n\n".join(f"[Page {d.metadata['page']}]\n{d.page_content}" for d in docs)
    answer = (ANSWER | llm | StrOutputParser()).invoke(
        {"context": context, "question": question})

    if answer.strip().startswith(NOT_FOUND):
        return answer, []
    import re
    cited = {int(x) for x in re.findall(r"\[Page (\d+)\]", answer)}
    sources, seen = [], set()
    for d in docs:
        p = d.metadata["page"]
        if p in seen or (cited and p not in cited):
            continue
        seen.add(p)
        sources.append({"page": p, "snippet": d.page_content[:220]})
    return answer, sorted(sources, key=lambda s: s["page"])


# ---------- analysis: map-reduce summary + structured extraction ----------
class RiskyClause(BaseModel):
    clause: str = Field(description="Short quote or paraphrase of the clause")
    page: int = Field(description="Page number where it appears")
    severity: str = Field(description="low, medium or high")
    explanation: str = Field(description="Why this could be a problem for the signer")


class Analysis(BaseModel):
    summary: str = Field(description="Short summary of this part of the document")
    parties: List[str] = Field(default_factory=list)
    key_dates: List[str] = Field(default_factory=list)
    obligations: List[str] = Field(default_factory=list)
    penalties: List[str] = Field(default_factory=list)
    termination_terms: List[str] = Field(default_factory=list)
    risky_clauses: List[RiskyClause] = Field(default_factory=list)


MAP = ChatPromptTemplate.from_template(
    "You review contracts for the person signing them. From the excerpt below, extract "
    "parties, key dates/deadlines, obligations, penalties, termination terms, and risky "
    "clauses (auto-renewal, one-sided liability, unusual fees, broad waivers, etc.). "
    "Only use what is in the text; leave lists empty if nothing applies.\n\n{text}")

REDUCE = ChatPromptTemplate.from_template(
    "Combine these partial summaries of one document into a single clear summary of "
    "at most 150 words, covering purpose, key obligations and notable risks.\n\n{text}")


def _dedupe(items):
    return list(dict.fromkeys(i.strip() for i in items if i.strip()))


def analyze_document(doc_id, group_chars=12000):
    data = get_vectorstore().get(where={"doc_id": doc_id})
    pieces = sorted(zip(data["documents"], data["metadatas"]), key=lambda x: x[1]["page"])
    groups, cur = [], ""
    for text, meta in pieces:
        line = f"[Page {meta['page']}] {text}\n"
        if len(cur) + len(line) > group_chars and cur:
            groups.append(cur)
            cur = ""
        cur += line
    if cur:
        groups.append(cur)

    extractor = MAP | get_llm().with_structured_output(Analysis)
    parts = extractor.batch([{"text": g} for g in groups])      # map

    summary = (REDUCE | get_llm() | StrOutputParser()).invoke(   # reduce
        {"text": "\n\n".join(p.summary for p in parts)})
    merged = {"summary": summary}
    for field in ("parties", "key_dates", "obligations", "penalties", "termination_terms"):
        merged[field] = _dedupe(x for p in parts for x in getattr(p, field))
    risks = [r.model_dump() for p in parts for r in p.risky_clauses]
    order = {"high": 0, "medium": 1, "low": 2}
    merged["risky_clauses"] = sorted(risks, key=lambda r: order.get(r["severity"].lower(), 3))
    return merged


COMPARE = ChatPromptTemplate.from_template(
    "Compare two documents using only the analyses below. Cover: key differences in "
    "obligations, costs/penalties, termination terms and risks, then state which is "
    "more favourable to the signer and why. Use plain language, short bullet points. "
    "You are not a lawyer.\n\nDocument A ({name_a}):\n{a}\n\nDocument B ({name_b}):\n{b}")


def compare_documents(name_a, analysis_a, name_b, analysis_b):
    return (COMPARE | get_llm() | StrOutputParser()).invoke({
        "name_a": name_a, "a": json.dumps(analysis_a, indent=1),
        "name_b": name_b, "b": json.dumps(analysis_b, indent=1)})
