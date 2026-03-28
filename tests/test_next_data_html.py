"""Tests for __NEXT_DATA__ extraction from raw HTML (bypassing lxml truncation)."""

import json

from cinemagoerng.registry import extract_next_data_from_html


def test_extract_next_data_from_html_simple() -> None:
    inner = {"props": {"pageProps": {"k": 1}}, "buildId": "x"}
    blob = json.dumps(inner, separators=(",", ":"))
    html = f'<!doctype html><script id="__NEXT_DATA__" type="application/json">{blob}</script>'
    out = extract_next_data_from_html(html)
    assert out == inner


def test_extract_next_data_stops_at_closing_script_tag() -> None:
    """Decoder must not read past the root JSON object into following HTML."""
    inner = {"props": {"pageProps": {"k": 1}}, "other": 2}
    blob = json.dumps(inner, separators=(",", ":"))
    html = (
        f'<script id="__NEXT_DATA__" type="application/json">{blob}</script>'
        "<p>not-json</p>"
    )
    out = extract_next_data_from_html(html)
    assert out == inner


def test_extract_next_data_script_close_inside_json_string() -> None:
    """``</script>`` inside a JSON string must not truncate the payload."""
    inner = {
        "props": {"pageProps": {"html": "foo </script> bar"}},
        "buildId": "x",
    }
    blob = json.dumps(inner, separators=(",", ":"))
    html = f'<script id="__NEXT_DATA__" type="application/json">{blob}</script>'
    out = extract_next_data_from_html(html)
    assert out == inner


def test_extract_next_data_type_attr_first() -> None:
    inner = {"props": {}, "a": 1}
    blob = json.dumps(inner)
    html = f'<script type="application/json" id=\'__NEXT_DATA__\'>{blob}</script>'
    assert extract_next_data_from_html(html) == inner


def test_extract_next_data_missing_returns_none() -> None:
    assert extract_next_data_from_html("<html><body></body></html>") is None
