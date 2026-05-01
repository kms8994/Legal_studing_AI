class EmbeddingClient:
    async def embed_text(self, text: str) -> list[float]:
        raise NotImplementedError("Embedding provider is not configured yet.")

