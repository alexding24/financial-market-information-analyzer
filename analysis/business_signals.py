from __future__ import annotations

import re
from dataclasses import dataclass


DEFAULT_KEYWORDS = [
    "AI",
    "artificial intelligence",
    "data center",
    "cloud",
    "GPU",
    "semiconductor",
    "demand",
    "margin",
    "inventory",
    "capex",
    "guidance",
    "competition",
    "regulation",
    "China",
]

SOURCE_LABELS = {
    "earnings_call": "Earnings call",
    "meeting": "Meeting",
    "tenk": "10-K",
}

FUTURE_SIGNAL_PATTERNS = [
    r"[^.!?\n]*(?:expect|expects|expected|forecast|guidance|outlook|plan|plans|planned|invest|investment|expand|growth|demand|opportunity|risk|margin|capacity|launch|roadmap)[^.!?\n]*[.!?]?",
    r"[^。！？\n]*(?:预计|展望|指引|计划|投资|扩张|增长|需求|机会|风险|利润率|产能|推出|路线图|未来)[^。！？\n]*[。！？]?",
]


@dataclass(frozen=True)
class SourceDocument:
    source_type: str
    text: str

    @property
    def label(self) -> str:
        return SOURCE_LABELS.get(self.source_type, self.source_type)


@dataclass(frozen=True)
class KeywordMention:
    keyword: str
    earnings_call: int
    meeting: int
    tenk: int
    total: int


@dataclass(frozen=True)
class BusinessSignalSummary:
    future_direction: str
    keyword_mentions: list[KeywordMention]
    source_count: int


def parse_keywords(raw_keywords: str | None) -> list[str]:
    if not raw_keywords:
        return DEFAULT_KEYWORDS

    keywords: list[str] = []
    for part in re.split(r"[,，\n]+", raw_keywords):
        keyword = part.strip()
        if keyword and keyword.lower() not in [item.lower() for item in keywords]:
            keywords.append(keyword)
    return keywords or DEFAULT_KEYWORDS


def _count_keyword(text: str, keyword: str) -> int:
    if not text.strip():
        return 0
    if re.search(r"[\u4e00-\u9fff]", keyword):
        return len(re.findall(re.escape(keyword), text, flags=re.IGNORECASE))
    return len(re.findall(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE))


def _extract_signal_sentences(documents: list[SourceDocument], max_sentences: int = 6) -> list[str]:
    sentences: list[str] = []
    for document in documents:
        text = " ".join(document.text.split())
        for pattern in FUTURE_SIGNAL_PATTERNS:
            for match in re.findall(pattern, text, flags=re.IGNORECASE):
                sentence = match.strip()
                if sentence and sentence not in sentences:
                    sentences.append(f"{document.label}: {sentence}")
                if len(sentences) >= max_sentences:
                    return sentences
    return sentences


def analyze_business_signals(
    documents: list[SourceDocument],
    keywords: list[str] | None = None,
) -> BusinessSignalSummary | None:
    clean_documents = [document for document in documents if document.text.strip()]
    if not clean_documents:
        return None

    clean_keywords = keywords or DEFAULT_KEYWORDS
    mentions: list[KeywordMention] = []
    for keyword in clean_keywords:
        earnings_call = sum(
            _count_keyword(document.text, keyword)
            for document in clean_documents
            if document.source_type == "earnings_call"
        )
        meeting = sum(
            _count_keyword(document.text, keyword)
            for document in clean_documents
            if document.source_type == "meeting"
        )
        tenk = sum(
            _count_keyword(document.text, keyword)
            for document in clean_documents
            if document.source_type == "tenk"
        )
        total = earnings_call + meeting + tenk
        if total:
            mentions.append(
                KeywordMention(
                    keyword=keyword,
                    earnings_call=earnings_call,
                    meeting=meeting,
                    tenk=tenk,
                    total=total,
                )
            )

    mentions.sort(key=lambda item: item.total, reverse=True)
    signal_sentences = _extract_signal_sentences(clean_documents)
    if signal_sentences:
        future_direction = "\n".join(f"- {sentence}" for sentence in signal_sentences)
    else:
        future_direction = "- 暂未从输入内容中识别到明确的未来计划、需求、风险或指引表述。"

    return BusinessSignalSummary(
        future_direction=future_direction,
        keyword_mentions=mentions,
        source_count=len(clean_documents),
    )


def format_business_signal_report(summary: BusinessSignalSummary | None) -> str:
    if summary is None:
        return ""

    keyword_table = "| 关键词 | Earnings call | Meeting | 10-K | 合计 |\n"
    keyword_table += "| --- | ---: | ---: | ---: | ---: |\n"
    if summary.keyword_mentions:
        for mention in summary.keyword_mentions:
            keyword_table += (
                f"| {mention.keyword} | {mention.earnings_call} | {mention.meeting} | "
                f"{mention.tenk} | {mention.total} |\n"
            )
    else:
        keyword_table += "| 暂无命中 | 0 | 0 | 0 | 0 |\n"

    return f"""## 业务动向和关键词信号

已分析重要场合数量：{summary.source_count}

### 未来动向线索

{summary.future_direction}

### 关键词提及次数

{keyword_table}

说明：这里统计的是你提供的 earnings call、meeting、10-K 文本或摘要里的关键词出现次数。输入内容越完整，结果越有参考价值。
"""
