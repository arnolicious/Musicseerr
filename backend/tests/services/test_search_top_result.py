"""Tests for SearchService._detect_top_result and _tokens_match."""

import pytest

from models.search import SearchResult
from services.search_service import SearchService, TOP_RESULT_SCORE_THRESHOLD


def _make_result(title: str, score: int = 100, type: str = "artist") -> SearchResult:
    return SearchResult(
        type=type,
        title=title,
        musicbrainz_id="00000000-0000-0000-0000-000000000001",
        score=score,
    )


class TestTokensMatch:
    """Tests for SearchService._tokens_match (prefix-aware token matching)."""

    def test_exact_match(self) -> None:
        assert SearchService._tokens_match({"taylor", "swift"}, {"taylor", "swift"}) is True

    def test_query_subset_of_title(self) -> None:
        assert SearchService._tokens_match({"taylor"}, {"taylor", "swift"}) is True

    def test_title_subset_of_query(self) -> None:
        assert SearchService._tokens_match({"taylor", "swift"}, {"swift"}) is True

    def test_prefix_match_query_partial(self) -> None:
        assert SearchService._tokens_match({"taylor", "swif"}, {"taylor", "swift"}) is True

    def test_prefix_match_single_partial(self) -> None:
        assert SearchService._tokens_match({"tay"}, {"taylor", "swift"}) is True

    def test_single_char_prefix_rejected(self) -> None:
        assert SearchService._tokens_match({"t"}, {"taylor", "swift"}) is False

    def test_prefix_match_title_shorter(self) -> None:
        assert SearchService._tokens_match({"taylor", "swift"}, {"tay"}) is True

    def test_no_match(self) -> None:
        assert SearchService._tokens_match({"radiohead"}, {"taylor", "swift"}) is False

    def test_partial_overlap_no_prefix(self) -> None:
        assert SearchService._tokens_match({"taylor", "jones"}, {"taylor", "swift"}) is False

    def test_empty_sets(self) -> None:
        # all() on empty iterable is vacuously True; _detect_top_result guards empty tokens
        assert SearchService._tokens_match(set(), {"taylor"}) is True
        assert SearchService._tokens_match({"taylor"}, set()) is True
        assert SearchService._tokens_match(set(), set()) is True


class TestDetectTopResult:
    """Tests for SearchService._detect_top_result."""

    def test_returns_none_for_empty_results(self) -> None:
        assert SearchService._detect_top_result([], "taylor swift") is None

    def test_returns_none_below_threshold(self) -> None:
        result = _make_result("Taylor Swift", score=TOP_RESULT_SCORE_THRESHOLD - 1)
        assert SearchService._detect_top_result([result], "taylor swift") is None

    def test_returns_result_at_threshold(self) -> None:
        result = _make_result("Taylor Swift", score=TOP_RESULT_SCORE_THRESHOLD)
        top = SearchService._detect_top_result([result], "taylor swift")
        assert top is result

    def test_exact_query_match(self) -> None:
        result = _make_result("Taylor Swift", score=100)
        top = SearchService._detect_top_result([result], "Taylor Swift")
        assert top is result

    def test_partial_query_prefix_match(self) -> None:
        result = _make_result("Taylor Swift", score=100)
        top = SearchService._detect_top_result([result], "Taylor Swif")
        assert top is result

    def test_single_token_prefix(self) -> None:
        result = _make_result("Taylor Swift", score=100)
        top = SearchService._detect_top_result([result], "Tay")
        assert top is result

    def test_query_superset_of_title(self) -> None:
        result = _make_result("Swift", score=95)
        top = SearchService._detect_top_result([result], "Taylor Swift")
        assert top is result

    def test_no_token_overlap(self) -> None:
        result = _make_result("Radiohead", score=95)
        top = SearchService._detect_top_result([result], "Taylor Swift")
        assert top is None

    def test_only_checks_first_result(self) -> None:
        low = _make_result("Radiohead", score=80)
        high = _make_result("Taylor Swift", score=100)
        assert SearchService._detect_top_result([low, high], "Taylor Swift") is None

    def test_diacritics_normalized(self) -> None:
        result = _make_result("Beyoncé", score=100)
        top = SearchService._detect_top_result([result], "beyonce")
        assert top is result

    def test_album_type(self) -> None:
        result = _make_result("Midnights", score=95, type="album")
        top = SearchService._detect_top_result([result], "Midnights")
        assert top is result
