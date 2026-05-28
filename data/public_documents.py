from __future__ import annotations

import os
import re
from dataclasses import dataclass

import requests
import yfinance as yf
from bs4 import BeautifulSoup

from analysis.business_signals import SourceDocument


SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"
FILING_SIGNAL_TERMS = [
    "ai",
    "data center",
    "cloud",
    "gpu",
    "demand",
    "growth",
    "revenue",
    "margin",
    "inventory",
    "supply",
    "capacity",
    "customer",
    "competition",
    "risk",
    "china",
    "export",
    "regulation",
    "outlook",
]


@dataclass(frozen=True)
class PublicDocumentResult:
    documents: list[SourceDocument]
    notes: list[str]


def _request_headers() -> dict[str, str]:
    return {
        "User-Agent": os.getenv("SEC_USER_AGENT", "financial-market-analyzer/0.1 research@example.com"),
        "Accept-Encoding": "gzip, deflate",
    }


def _clean_text(text: str, max_chars: int = 20_000) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    return clean[:max_chars]


def _clean_sec_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    for tag in list(soup.find_all()):
        if tag.parent is None:
            continue
        tag_name = tag.name or ""
        style = tag.attrs.get("style", "") if tag.attrs else ""
        if tag_name.startswith(("ix:", "xbrli:", "xbrldi:", "link:", "xlink:")) or "display:none" in style.replace(" ", "").lower():
            tag.decompose()
    return _clean_text(soup.get_text(" "), max_chars=120_000)


def _extract_relevant_filing_text(text: str, max_sentences: int = 80) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    selected: list[str] = []
    for sentence in sentences:
        lowered = sentence.lower()
        if 40 <= len(sentence) <= 600 and any(term in lowered for term in FILING_SIGNAL_TERMS):
            selected.append(sentence.strip())
        if len(selected) >= max_sentences:
            break
    return _clean_text(" ".join(selected), max_chars=30_000) or text[:30_000]


def _news_text_from_item(item: dict) -> str:
    content = item.get("content") if isinstance(item.get("content"), dict) else {}
    title = item.get("title") or content.get("title") or ""
    summary = item.get("summary") or content.get("summary") or ""
    publisher = item.get("publisher") or content.get("provider", {}).get("displayName") or ""
    return _clean_text(" ".join(part for part in [publisher, title, summary] if part))


def _classify_news_source(text: str) -> str:
    lowered = text.lower()
    if any(term in lowered for term in ["earnings", "results", "quarter", "guidance", "outlook"]):
        return "earnings_call"
    if any(term in lowered for term in ["investor day", "conference", "presentation", "meeting"]):
        return "meeting"
    return "news"


def _company_terms(symbol: str, company_name: str | None) -> list[str]:
    terms = [symbol.lower()]
    if company_name:
        words = re.findall(r"[A-Za-z][A-Za-z0-9]+", company_name)
        for word in words:
            lowered = word.lower()
            if lowered not in {"inc", "corp", "corporation", "ltd", "plc", "class", "company"}:
                terms.append(lowered)
    return list(dict.fromkeys(terms))


def fetch_yahoo_news_documents(symbol: str, company_name: str | None = None, max_items: int = 8) -> PublicDocumentResult:
    try:
        news_items = yf.Ticker(symbol).news or []
    except Exception as exc:
        return PublicDocumentResult([], [f"{symbol}: Yahoo Finance 新闻读取失败：{exc}"])

    terms = _company_terms(symbol, company_name)
    documents: list[SourceDocument] = []
    for item in news_items:
        text = _news_text_from_item(item)
        lowered = text.lower()
        if text and any(term in lowered for term in terms):
            documents.append(SourceDocument(_classify_news_source(text), text))
        if len(documents) >= max_items:
            break

    notes = [f"{symbol}: 自动读取 Yahoo Finance 新闻摘要 {len(documents)} 条。"] if documents else [f"{symbol}: 没有读取到 Yahoo Finance 新闻摘要。"]
    return PublicDocumentResult(documents, notes)


def _ticker_to_cik(symbol: str) -> str | None:
    response = requests.get(SEC_COMPANY_TICKERS_URL, headers=_request_headers(), timeout=20)
    response.raise_for_status()
    companies = response.json()
    for company in companies.values():
        if str(company.get("ticker", "")).upper() == symbol.upper():
            return str(company.get("cik_str", "")).zfill(10)
    return None


def _latest_filing_metadata(cik: str, forms: set[str]) -> tuple[str, str, str] | None:
    response = requests.get(SEC_SUBMISSIONS_URL.format(cik=cik), headers=_request_headers(), timeout=20)
    response.raise_for_status()
    recent = response.json().get("filings", {}).get("recent", {})
    form_values = recent.get("form", [])
    accession_values = recent.get("accessionNumber", [])
    document_values = recent.get("primaryDocument", [])

    for form, accession, document in zip(form_values, accession_values, document_values):
        if form in forms:
            return form, accession, document
    return None


def fetch_sec_filing_document(symbol: str, forms: set[str] | None = None) -> PublicDocumentResult:
    target_forms = forms or {"10-K", "10-Q"}
    try:
        cik = _ticker_to_cik(symbol)
        if not cik:
            return PublicDocumentResult([], [f"{symbol}: SEC 没有找到对应 CIK。"])

        filing = _latest_filing_metadata(cik, target_forms)
        if not filing:
            return PublicDocumentResult([], [f"{symbol}: SEC 最近申报里没有找到 10-K / 10-Q。"])

        form, accession, document = filing
        archive_url = SEC_ARCHIVE_URL.format(
            cik=str(int(cik)),
            accession=accession.replace("-", ""),
            document=document,
        )
        response = requests.get(archive_url, headers=_request_headers(), timeout=30)
        response.raise_for_status()
        text = _extract_relevant_filing_text(_clean_sec_html(response.text))
        return PublicDocumentResult(
            [SourceDocument("tenk", f"{form} filing from SEC. {text}")],
            [f"{symbol}: 自动读取 SEC 最近 {form}：{document}。"],
        )
    except Exception as exc:
        return PublicDocumentResult([], [f"{symbol}: SEC 申报读取失败：{exc}"])


def fetch_public_documents(symbol: str, company_name: str | None = None) -> PublicDocumentResult:
    documents: list[SourceDocument] = []
    notes: list[str] = []

    for result in [fetch_yahoo_news_documents(symbol, company_name), fetch_sec_filing_document(symbol)]:
        documents.extend(result.documents)
        notes.extend(result.notes)

    return PublicDocumentResult(documents, notes)
