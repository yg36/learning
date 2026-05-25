import re

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingEngine:
    """Library-backed semantic scorer for product retrieval.

    This is still local and lightweight, but now uses scikit-learn's tested
    vectorization and cosine similarity stack instead of a handmade TF-IDF
    implementation. A transformer or FAISS backend can sit behind the same
    add_similarity_scores contract later.
    """

    BACKEND = "sklearn_tfidf_vectorizer_v1"

    TEXT_COLUMNS = [
        "semantic_document",
        "content_embedding_text",
        "product_title",
        "product_type",
        "key_ingredients",
        "product_tags",
        "target_concerns",
        "routine_compatibility_tags",
    ]

    def __init__(self, df=None):
        self.vectorizer = TfidfVectorizer(
            preprocessor=self._preprocess,
            token_pattern=r"(?u)\b[a-z0-9][a-z0-9]+\b",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
            norm="l2",
        )
        self._is_fitted = False

        documents = []
        if df is not None and not df.empty:
            documents = [self._document_text(row) for _, row in df.iterrows()]

        if documents:
            self.vectorizer.fit(documents)
            self._is_fitted = True

    def add_similarity_scores(self, df, user):
        result = df.copy()
        if result.empty:
            result["semantic_similarity_score"] = []
            result["semantic_backend"] = self.BACKEND
            return result

        query_text = self._query_text(user)
        documents = [self._document_text(row) for _, row in result.iterrows()]
        result["semantic_similarity_score"] = self.score_texts(query_text, documents)
        result["semantic_backend"] = self.BACKEND
        return result

    def score_texts(self, query, documents):
        if not documents:
            return []

        if not self._is_fitted:
            self.vectorizer.fit(documents + [query])
            self._is_fitted = True

        query_vector = self.vectorizer.transform([query])
        document_matrix = self.vectorizer.transform(documents)
        scores = cosine_similarity(query_vector, document_matrix).ravel()
        return [round(float(score), 4) for score in scores]

    def _query_text(self, user):
        parts = [
            user.get("query", ""),
            user.get("normalized_query", ""),
            user.get("product_type", ""),
            " ".join(_as_list(user.get("skin_concerns"))),
            " ".join(_as_list(user.get("requested_ingredients"))),
            " ".join(_as_list(user.get("avoided_ingredients"))),
            user.get("matched_catalog_product", ""),
        ]
        return " ".join(str(part) for part in parts if part)

    def _document_text(self, row):
        if isinstance(row, pd.Series):
            values = [str(row.get(column, "")) for column in self.TEXT_COLUMNS if column in row.index]
        else:
            values = [str(row.get(column, "")) for column in self.TEXT_COLUMNS]
        return " ".join(values)

    def _preprocess(self, text):
        text = str(text).lower().replace("-", " ")
        words = re.findall(r"[a-z0-9]+", text)
        expanded = []
        for word in words:
            expanded.append(word)
            if len(word) > 3 and word.endswith("s"):
                expanded.append(word[:-1])
        return " ".join(expanded)


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]
