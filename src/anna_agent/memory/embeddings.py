import hashlib
import math
import re

from openai import OpenAI


class HashEmbeddingProvider:
    def __init__(self, dimension: int):
        self.dimension = dimension

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = re.findall(r"[\w]+|[\u4e00-\u9fff]", text.lower())
        for token in tokens or [text]:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimension
            sign = 1.0 if digest[8] % 2 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAIEmbeddingProvider:
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(model=self.model_name, input=texts)
        return [item.embedding for item in response.data]


class EmbeddingService:
    def __init__(self, config):
        self.config = config
        self.hash_provider = HashEmbeddingProvider(config.embedding_dimension)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            api_key = self.config.embedding_api_key or self.config.api_key
            base_url = self.config.embedding_base_url or self.config.base_url
            provider = OpenAIEmbeddingProvider(
                api_key=api_key,
                base_url=base_url,
                model_name=self.config.embedding_model_name,
            )
            vectors = provider.embed_texts(texts)
            if vectors:
                return vectors
        except Exception:
            pass
        return self.hash_provider.embed_texts(texts)

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]
