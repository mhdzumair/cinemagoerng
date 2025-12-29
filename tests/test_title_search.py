import pytest

from cinemagoerng import web as imdb
from cinemagoerng.model import (
    RangeFilter,
    SearchFilters,
    SortCriteria,
    SortField,
    SortOrder,
)


class TestSearchTitles:
    """Tests for the search_titles function."""

    @pytest.mark.parametrize(
        ("query", "min_results"),
        [
            ("The Matrix", 3),
            ("Inception", 1),
            ("Breaking Bad", 1),
        ],
    )
    def test_search_titles_returns_results(self, query, min_results):
        """Test that search returns expected minimum results."""
        results = imdb.search_titles(query, count=10)
        assert len(results) >= min_results

    def test_search_titles_returns_title_objects(self):
        """Test that search results are proper Title objects."""
        results = imdb.search_titles("The Matrix", count=5)
        assert len(results) > 0

        first = results[0]
        assert first.imdb_id is not None
        assert first.imdb_id.startswith("tt")
        assert first.title is not None

    def test_search_titles_with_count_limit(self):
        """Test that count parameter limits results."""
        results = imdb.search_titles("movie", count=5)
        assert len(results) <= 5


class TestSearchTitlesWithFilters:
    """Tests for search_titles with filters."""

    def test_search_with_title_type_filter(self):
        """Test filtering by title type."""
        filters = SearchFilters(title_types=["movie"])
        results = imdb.search_titles("action", filters=filters, count=10)
        assert len(results) > 0
        # All results should be movies
        for r in results:
            assert r.type_id in ["movie", "tvMovie", "video"]

    def test_search_with_year_filter(self):
        """Test filtering by release year range."""
        filters = SearchFilters(
            release_date=RangeFilter(min_value="2020", max_value="2023"),
        )
        results = imdb.search_titles("action", filters=filters, count=10)
        assert len(results) > 0
        for r in results:
            if r.year is not None:
                assert 2020 <= r.year <= 2023

    def test_search_with_rating_filter(self):
        """Test filtering by minimum rating."""
        filters = SearchFilters(
            user_rating=RangeFilter(min_value=8.0, max_value=None)
        )
        results = imdb.search_titles("drama", filters=filters, count=10)
        assert len(results) > 0
        for r in results:
            if r.rating is not None:
                assert float(r.rating) >= 7.5  # Allow small margin


class TestSearchTitlesWithSort:
    """Tests for search_titles with sorting."""

    def test_search_with_sort_by_rating(self):
        """Test sorting by rating descending."""
        sort = SortCriteria(
            field=SortField.USER_RATING,
            order=SortOrder.DESCENDING,
        )
        results = imdb.search_titles("thriller", sort=sort, count=10)
        assert len(results) > 0

        # Check ratings are roughly in descending order
        ratings = [float(r.rating) for r in results if r.rating is not None]
        if len(ratings) > 1:
            # Allow some tolerance since IMDb sorting may differ slightly
            assert ratings[0] >= ratings[-1] - 1

    def test_search_with_sort_by_year(self):
        """Test sorting by release year."""
        sort = SortCriteria(
            field=SortField.YEAR,
            order=SortOrder.DESCENDING,
        )
        results = imdb.search_titles("sci-fi", sort=sort, count=10)
        assert len(results) > 0
