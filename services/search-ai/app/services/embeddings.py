from __future__ import annotations

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import get_settings
from app.services.text_prep import TOKEN_RE

_FALLBACK_DIMENSION = 256


class EmbeddingsProvider:
    """
    Provee vectores densos para consultas y documentos.

    Si `sentence-transformers` (extra [ml]) está instalado, usa un modelo de
    Sentence Transformers en español (configurable vía EMBEDDING_MODEL, por
    defecto BAAI/bge-small-es-v1.5) para embeddings semánticos reales. En caso
    contrario, cae a una representación TF-IDF + SVD determinista y ligera,
    apta para CI y entornos sin GPU. El buscador es transparente a la elección.
    """

    def __init__(self, model: str | None = None) -> None:
        self.model = model or get_settings().embedding_model
        self._st = None
        self._vectorizer = TfidfVectorizer(
            token_pattern=TOKEN_RE,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
        )
        self._svd: TruncatedSVD | None = None
        self._dim = 0
        self._fitted = False

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def ml_enabled(self) -> bool:
        return self._st is not None

    def fit(self, texts: list[str]) -> EmbeddingsProvider:
        if not texts:
            raise ValueError("Necesito al menos un documento para construir los embeddings")
        self._load_st()
        if self._st is not None:
            self._fitted = True
            return self

        matrix = self._vectorizer.fit_transform(texts)
        dimension = min(_FALLBACK_DIMENSION, max(2, matrix.shape[0] - 1), matrix.shape[1])
        self._svd = TruncatedSVD(n_components=dimension, random_state=42).fit(matrix)
        self._dim = dimension
        self._fitted = True
        return self

    def embed(self, texts: list[str]) -> np.ndarray:
        if not self._fitted:
            raise RuntimeError("fit() debe ejecutarse antes de embed()")
        if self._st is not None:
            vectors = self._st.encode(texts, normalize_embeddings=True)
            return np.asarray(vectors, dtype=np.float32)

        matrix = self._vectorizer.transform(texts)
        vectors = self._svd.transform(matrix).astype(np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return vectors / norms

    def embed_one(self, text: str) -> np.ndarray:
        return self.embed([text])[0]

    def _load_st(self) -> None:
        if self.model:
            try:
                from sentence_transformers import SentenceTransformer

                self._st = SentenceTransformer(self.model)
                self._dim = self._st.get_sentence_embedding_dimension()
            except Exception:  # noqa: BLE001
                self._st = None
