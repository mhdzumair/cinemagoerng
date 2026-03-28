from cinemagoerng import model
from cinemagoerng.web import _title_data_from_suggestion_payload, deserialize


def test_suggestion_payload_maps_matrix() -> None:
    payload = {
        "d": [
            {"id": "/spotlight/", "l": "Spotlight"},
            {
                "id": "tt0133093",
                "l": "The Matrix",
                "qid": "movie",
                "y": 1999,
                "i": {
                    "imageUrl": "https://example.com/poster.jpg",
                    "height": 100,
                    "width": 100,
                },
            },
        ],
        "q": "tt0133093",
        "v": 1,
    }
    data = _title_data_from_suggestion_payload("tt0133093", payload)
    assert data is not None
    title = deserialize(data, model.Title)
    assert title.imdb_id == "tt0133093"
    assert title.title == "The Matrix"
    assert title.type_id == "movie"
    assert title.year == 1999
    assert title.primary_image == "https://example.com/poster.jpg"


def test_suggestion_payload_no_match() -> None:
    assert (
        _title_data_from_suggestion_payload(
            "tt0999999",
            {"d": [{"id": "tt0133093", "l": "Other", "qid": "movie"}], "v": 1},
        )
        is None
    )
