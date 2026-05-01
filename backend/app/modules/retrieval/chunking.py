def split_text(text: str, *, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return [chunk for chunk in chunks if chunk.strip()]


def chunk_document(
    text: str,
    *,
    source_type: str,
    source_name: str,
    source_url: str,
    case_number: str | None = None,
    law_article: str | None = None,
    chunk_size: int = 1200,
    overlap: int = 150,
) -> list[dict[str, object]]:
    chunks = split_text(text, chunk_size=chunk_size, overlap=overlap)
    return [
        {
            "id": f"{source_type}:{source_name}:{index}",
            "source_type": source_type,
            "source_name": source_name,
            "source_url": source_url,
            "case_number": case_number,
            "law_article": law_article,
            "chunk_text": chunk,
            "chunk_index": index,
            "retrieval_score": 1.0,
        }
        for index, chunk in enumerate(chunks)
    ]
