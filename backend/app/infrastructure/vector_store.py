class VectorStore:
    async def search(self, query_embedding: list[float], *, top_k: int) -> list[dict[str, object]]:
        raise NotImplementedError("Vector store is not configured yet.")

