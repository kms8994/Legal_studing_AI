from app.modules.retrieval.schemas import EvidenceChunk


def rank_chunks(chunks: list[EvidenceChunk]) -> list[EvidenceChunk]:
    return sorted(chunks, key=lambda chunk: chunk.retrieval_score, reverse=True)


def filter_ranked_chunks(
    chunks: list[EvidenceChunk],
    *,
    top_k: int,
    score_threshold: float,
) -> list[EvidenceChunk]:
    ranked = rank_chunks(chunks)
    return [
        chunk
        for chunk in ranked
        if chunk.retrieval_score >= score_threshold
    ][:top_k]
