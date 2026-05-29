from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

from analysis.i18n import Language


@dataclass(frozen=True)
class NewsLink:
    title: str
    url: str
    source: str


def _dedupe_links(links: list[NewsLink]) -> list[NewsLink]:
    seen: set[str] = set()
    unique: list[NewsLink] = []
    for link in links:
        if not link.url or link.url in seen:
            continue
        seen.add(link.url)
        unique.append(link)
    return unique


def market_news_links(
    symbol: str,
    company_name: str | None,
    sector: str | None,
    industry: str | None,
    discovered_links: list[NewsLink] | None = None,
    language: Language = "zh",
) -> str:
    links = _dedupe_links(discovered_links or [])
    query_parts = [company_name or symbol, sector or "", industry or ""]
    company_query = quote_plus(company_name or symbol)
    industry_query = quote_plus(" ".join(part for part in query_parts if part).strip())

    fallback_links = [
        NewsLink(
            "Yahoo Finance stock news" if language == "en" else "Yahoo Finance 股票新闻",
            f"https://finance.yahoo.com/quote/{quote_plus(symbol)}/news/",
            "Yahoo Finance",
        ),
        NewsLink(
            "Google News company search" if language == "en" else "Google News 公司新闻搜索",
            f"https://news.google.com/search?q={company_query}",
            "Google News",
        ),
    ]
    if industry_query and industry_query != company_query:
        fallback_links.append(
            NewsLink(
                "Google News industry search" if language == "en" else "Google News 行业新闻搜索",
                f"https://news.google.com/search?q={industry_query}",
                "Google News",
            )
        )

    links = _dedupe_links(links + fallback_links)
    if not links:
        return ""

    heading = "## Latest News and Filing Links" if language == "en" else "## 最新新闻与公告链接"
    note = (
        "These links open the source pages directly. Search links are included as a fallback when article links are unavailable."
        if language == "en"
        else "这些链接可以直达来源页面。若具体新闻链接不可用，会附上新闻搜索入口作为备用。"
    )
    items = "\n".join(f"- [{link.title}]({link.url}) - {link.source}" for link in links[:12])
    return f"{heading}\n\n{items}\n\n> {note}\n"
