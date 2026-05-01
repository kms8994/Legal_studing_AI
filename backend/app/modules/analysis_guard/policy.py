PROHIBITED_LEGAL_ADVICE_PATTERNS = (
    "승소할 수 있습니다",
    "대응해야 합니다",
    "문제없습니다",
    "반드시 인정됩니다",
    "소송을 제기하세요",
)


def contains_prohibited_legal_advice(text: str) -> bool:
    return any(pattern in text for pattern in PROHIBITED_LEGAL_ADVICE_PATTERNS)
