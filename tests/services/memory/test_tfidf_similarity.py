"""Tests for TF-IDF cosine similarity calculator."""

import pytest

from app.services.memory.tfidf_similarity import TfidfSimilarity


@pytest.fixture
def similarity():
    return TfidfSimilarity()


def test_identical_texts_high_similarity(similarity):
    """Identical texts should have very high similarity (>0.9)."""
    scores = similarity.calculate("python programming", ["python programming"])
    assert scores[0] > 0.9


def test_no_overlap_low_similarity(similarity):
    """Completely unrelated texts should have very low similarity (<0.1)."""
    scores = similarity.calculate(
        "cats dogs pets", ["mathematics physics calculus"]
    )
    assert scores[0] < 0.1


def test_partial_overlap_medium_similarity(similarity):
    """Texts with some shared words should have medium similarity."""
    scores = similarity.calculate(
        "python web framework", ["python flask web application"]
    )
    assert 0.3 < scores[0] < 0.8


def test_empty_query_returns_zeros(similarity):
    """Empty query should return list of 0.0 for each document."""
    scores = similarity.calculate("", ["some document"])
    assert scores == [0.0]


def test_empty_documents_returns_empty(similarity):
    """Empty document list should return empty list."""
    scores = similarity.calculate("any query", [])
    assert scores == []


def test_single_document(similarity):
    """Single document with partial overlap should return one positive score."""
    scores = similarity.calculate("weather forecast", ["today weather is sunny"])
    assert len(scores) == 1
    assert scores[0] > 0.0


def test_case_insensitive(similarity):
    """Similarity should be case-insensitive."""
    scores = similarity.calculate(
        "Python Programming", ["python programming basics"]
    )
    assert scores[0] > 0.3


def test_distinctive_words_score_higher(similarity):
    """Documents matching distinctive/rare query words should score higher."""
    scores = similarity.calculate(
        "diabetes medication",
        [
            "User takes metformin medication for diabetes",
            "User likes medication time",
        ],
    )
    assert scores[0] > scores[1]
