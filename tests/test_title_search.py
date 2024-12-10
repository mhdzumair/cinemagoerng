import pytest

from cinemagoerng import web


@pytest.mark.parametrize(
    (
        "query",
        "title_types",
        "expected_id",
        "expected_title",
        "expected_year",
        "expected_type",
    ),
    [
        (
            "The Matrix",
            ["movie"],
            "tt0133093",
            "The Matrix",
            1999,
            "movie",
        ),
        (
            "Breaking Bad",
            ["tvSeries"],
            "tt0903747",
            "Breaking Bad",
            2008,
            "tvSeries",
        ),
        ("Inception", ["movie"], "tt1375666", "Inception", 2010, "movie"),
    ],
)
def test_basic_search(
    query,
    title_types,
    expected_id,
    expected_title,
    expected_year,
    expected_type,
):
    results = web.search_title(query=query, title_types=title_types)

    # Verify we got results
    assert results

    # Find the expected result
    found = False
    for title in results:
        if title.imdb_id == expected_id:
            found = True
            assert title.title == expected_title
            assert title.year == expected_year
            assert title.type_id == expected_type
            break

    assert found, f"Expected title {expected_id} not found in search results"


@pytest.mark.parametrize(
    (
        "query",
        "genres",
        "release_date",
        "min_votes",
        "expected_count",
        "expected_genres",
    ),
    [
        (
            "Matrix",
            ["sci_fi", "action"],
            (1999, 1999),
            100000,
            1,
            ["Sci-Fi", "Action"],
        ),
        (
            "Lord of the Rings",
            ["adventure", "fantasy"],
            (2001, 2003),
            100000,
            3,
            ["Adventure", "Fantasy"],
        ),
    ],
)
def test_advanced_search(
    query, genres, release_date, min_votes, expected_count, expected_genres
):
    results = web.search_title(
        query=query,
        genres=genres,
        release_date=release_date,
        min_votes=min_votes,
    )

    # Verify number of results matches expectation
    matching_results = [
        title
        for title in results
        if (release_date[0] <= title.year <= release_date[1])
        and all(genre in title.genres for genre in expected_genres)
        and title.vote_count >= min_votes
    ]

    assert len(matching_results) >= expected_count


@pytest.mark.parametrize(
    ("query", "sort", "expected_order"),
    [
        (
            "Star Wars",
            "year,asc",
            ["tt0076759", "tt0080684", "tt0086190"],  # Episode IV, V, VI
        ),
        (
            "Lord of the Rings",
            "year,desc",
            [
                "tt32328070",
                "tt32869251",
                "tt14824600",
            ],
        ),
    ],
)
def test_search_sorting(query, sort, expected_order):
    results = web.search_title(query=query, sort=sort)

    # Get the IDs of matching titles in the order they appear
    result_ids = [
        title.imdb_id for title in results if title.imdb_id in expected_order
    ]

    # Check if the matching IDs appear in the expected order
    assert result_ids[: len(expected_order)] == expected_order


def test_empty_search():
    results = web.search_title()
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_with_invalid_parameters():
    # Should handle invalid genre gracefully
    results = web.search_title(query="Matrix", genres=["nonexistent_genre"])
    assert isinstance(results, list)

    # Should handle invalid date range gracefully
    results = web.search_title(
        query="Matrix",
        release_date=(2025, 2024),  # Invalid range
    )
    assert isinstance(results, list)


@pytest.mark.parametrize(
    ("query", "languages", "countries", "expected_lang", "expected_country"),
    [
        ("Seven Samurai", ["ja"], ["jp"], "Japanese", "Japan"),
        ("Life is Beautiful", ["it"], ["it"], "Italian", "Italy"),
    ],
)
def test_search_language_country(
    query, languages, countries, expected_lang, expected_country
):
    results = web.search_title(
        query=query, languages=languages, countries=countries
    )

    assert results
    title = results[0]

    # Update the title with additional information
    web.update_title(title, page="main", keys=["language_codes", "country_codes"])

    # Check if the expected language and country are in the results
    assert expected_lang in title.languages
    assert expected_country in title.countries
