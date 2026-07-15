import os
from typing import Any

import structlog

from rag.chunker import DocumentChunker

logger = structlog.get_logger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.model = None
        self.openai_client = None
        self._init_models()

    def _init_models(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            try:
                from openai import OpenAI

                self.openai_client = OpenAI(api_key=api_key)
            except ImportError:
                pass
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            logger.warning("sentence_transformers not available, using hash embeddings")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.openai_client:
            try:
                model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
                response = self.openai_client.embeddings.create(input=texts, model=model)
                return [item.embedding for item in response.data]
            except Exception as exc:
                logger.warning("openai_embedding_failed", error=str(exc))

        if self.model:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()

        return [self._hash_embed(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]

    def _hash_embed(self, text: str, dim: int = 384) -> list[float]:
        import hashlib

        result = []
        for i in range(dim):
            h = hashlib.sha256(f"{text}:{i}".encode()).digest()
            result.append((int.from_bytes(h[:4], "big") / 2**32) * 2 - 1)
        return result
