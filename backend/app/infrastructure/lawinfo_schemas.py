from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LawInfoSource:
    source_url: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CaseSummary:
    id: str
    title: str
    case_number: str | None
    court: str | None
    decision_date: str | None
    source_url: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CaseDocument:
    id: str
    title: str
    case_number: str | None
    body_text: str
    source_url: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StatuteArticle:
    law_id: str | None
    law_name: str
    article: str
    body_text: str
    source_url: str
    raw: dict[str, Any] = field(default_factory=dict)

