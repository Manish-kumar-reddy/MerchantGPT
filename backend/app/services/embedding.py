"""
Local, offline text embedding for chat-memory semantic search over pgvector.

No embeddings API key is required anywhere in this stack. This is a hashing
bag-of-words vector: each token is hashed into one of `dimension` buckets,
counted, and the resulting vector is L2-normalized so cosine similarity
(pgvector's `<=>` operator) behaves sensibly. It will not capture semantic
meaning the way a trained embedding model would -- two sentences about "churn"
and "customer attrition" will not score as similar -- but it reliably clusters
messages that share vocabulary, which is what chat-memory retrieval needs in
practice (a merchant asking about "the abandoned cart problem" twice will
retrieve the earlier turn). If a real embeddings provider is ever wired in,
only this module needs to change -- every caller just awaits `embed_text()`.
"""

import hashlib
import re
from math import sqrt

from app.core.config import get_settings

settings = get_settings()

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def embed_text(text: str, dimension: int | None = None) -> list[float]:
    dim = dimension or settings.embedding_dimension
    vector = [0.0] * dim

    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]
    return vector
