"""TF-IDF based text similarity calculator."""

from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TfidfSimilarity:
    """
    TF-IDF based text similarity calculator.

    Uses scikit-learn's TfidfVectorizer and cosine_similarity
    to calculate how similar a query is to a list of documents.
    Distinctive/rare words are weighted higher than common words.

    Usage:
        >>> similarity = TfidfSimilarity()
        >>> scores = similarity.calculate("diabetes medication", [
        ...     "User takes metformin for diabetes",
        ...     "User likes sunny weather"
        ... ])
        >>> scores[0] > scores[1]  # diabetes doc scores higher
        True
    """

    def calculate(self, query: str, documents: List[str]) -> List[float]:
        """
        Calculate TF-IDF cosine similarity between query and documents.

        Args:
            query: The search query string
            documents: List of document strings to compare against

        Returns:
            List of similarity scores (0.0 to 1.0), one per document.
            Empty list if documents is empty.
            All zeros if query is empty.
        """
        if not documents:
            return []

        if not query.strip():
            return [0.0] * len(documents)

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([query] + documents)
        return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0].tolist()
