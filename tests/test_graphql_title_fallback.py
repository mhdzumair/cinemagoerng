import json
from unittest.mock import patch

from cinemagoerng import model
from cinemagoerng.registry import imdb_title_type_text, strip_html
from cinemagoerng.web import (
    _get_title_from_graphql,
    _merge_graphql_title_scrape_parts,
    deserialize,
)


def test_strip_html_br_and_tags() -> None:
    assert (
        strip_html("a<br/>b<p>x</p>")
        == "a\nbx"
    )


def test_imdb_title_type_text_maps_movie() -> None:
    assert imdb_title_type_text("Movie") == "movie"
    assert imdb_title_type_text("TV Series") == "tvSeries"


def test_get_title_from_graphql_merges_topics_and_storyline() -> None:
    topics_body = {
        "data": {
            "title": {
                "originalTitleText": {"text": "The Matrix"},
                "primaryImage": {"url": "https://example.com/poster.jpg"},
                "titleType": {"text": "Movie", "canHaveEpisodes": False},
                "subNavRatings": {"aggregateRating": 8.7},
            }
        }
    }
    storyline_body = {
        "data": {
            "title": {
                "id": "tt0133093",
                "genres": {
                    "genres": [
                        {"id": "Action", "text": "Action"},
                        {"id": "Sci-Fi", "text": "Sci-Fi"},
                    ]
                },
                "taglines": {
                    "edges": [{"node": {"text": "Free your mind"}}],
                    "total": 15,
                },
                "certificate": {
                    "rating": "R",
                    "ratingReason": "Rated R for sci-fi violence",
                    "ratingsBody": {"id": "MPAA"},
                },
                "outlines": {
                    "edges": [
                        {
                            "node": {
                                "plotText": {
                                    "plaidHtml": "<p>Short outline</p>"
                                }
                            }
                        }
                    ]
                },
            }
        }
    }

    def fake_fetch(
        url: str,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict | None = None,
    ) -> str:
        if "operationName=TitleAllTopics" in url:
            return json.dumps(topics_body)
        if "operationName=Title_Storyline" in url:
            return json.dumps(storyline_body)
        raise AssertionError(f"unexpected url: {url!r}")

    with patch("cinemagoerng.web._http_client") as client:
        client.fetch = fake_fetch
        title = _get_title_from_graphql("tt0133093")
    assert title is not None
    assert title.imdb_id == "tt0133093"
    assert title.title == "The Matrix"
    assert title.type_id == "movie"
    assert title.primary_image == "https://example.com/poster.jpg"
    assert title.rating is not None and float(title.rating) == 8.7
    assert title.genres == ["Action", "Sci-Fi"]
    assert title.taglines == ["Free your mind"]
    assert title.certification is not None
    assert title.certification.mpa_rating == "R"
    assert title.plot.get("en") == "Short outline"


def test_get_title_from_graphql_returns_none_without_topics() -> None:
    def fake_fetch(
        url: str,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict | None = None,
    ) -> str:
        return json.dumps({"errors": [{"message": "nope"}]})

    with patch("cinemagoerng.web._http_client") as client:
        client.fetch = fake_fetch
        assert _get_title_from_graphql("tt0133093") is None


def test_get_title_from_graphql_returns_none_when_title_missing() -> None:
    def fake_fetch(
        url: str,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict | None = None,
    ) -> str:
        return json.dumps({"data": {"title": None}})

    with patch("cinemagoerng.web._http_client") as client:
        client.fetch = fake_fetch
        assert _get_title_from_graphql("tt0999999") is None


def test_storyline_only_merge_keeps_topics_fields() -> None:
    """Storyline scrape fills genres; type_id stays from TitleAllTopics."""
    merged = _merge_graphql_title_scrape_parts(
        {"title": "A", "type_id": "movie", "rating": None},
        {"genres": ["Drama"], "plot": {}},
    )
    t = deserialize(merged | {"imdb_id": "tt0000001"}, model.Title)
    assert t.title == "A"
    assert t.type_id == "movie"
    assert t.genres == ["Drama"]
