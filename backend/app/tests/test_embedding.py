from math import isclose

from app.services.embedding import embed_text


def test_embedding_has_requested_dimension():
    vec = embed_text("some text about churn and refunds", dimension=64)
    assert len(vec) == 64


def test_embedding_is_l2_normalized():
    vec = embed_text("revenue dropped this month", dimension=128)
    norm = sum(v * v for v in vec) ** 0.5
    assert isclose(norm, 1.0, abs_tol=1e-6)


def test_same_text_produces_identical_embedding():
    a = embed_text("abandoned cart recovery", dimension=64)
    b = embed_text("abandoned cart recovery", dimension=64)
    assert a == b


def test_empty_text_returns_zero_vector_not_an_error():
    vec = embed_text("", dimension=32)
    assert vec == [0.0] * 32


def test_shared_vocabulary_scores_more_similar_than_unrelated_text():
    def cosine(a, b):
        return sum(x * y for x, y in zip(a, b))  # both already unit-normalized

    base = embed_text("customers are abandoning their carts before checkout", dimension=256)
    related = embed_text("cart abandonment is a checkout problem for customers", dimension=256)
    unrelated = embed_text("the weather forecast predicts rain tomorrow", dimension=256)

    assert cosine(base, related) > cosine(base, unrelated)
