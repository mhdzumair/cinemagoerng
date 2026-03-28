"""Tests for __NEXT_DATA__ extraction from raw HTML (bypassing lxml truncation)."""

import json

from cinemagoerng.registry import extract_next_data_from_html


def test_extract_next_data_from_html_simple() -> None:
    inner = {"props": {"pageProps": {"k": 1}}, "buildId": "x"}
    blob = json.dumps(inner, separators=(",", ":"))
    html = f'<!doctype html><script id="__NEXT_DATA__" type="application/json">{blob}</script>'
    out = extract_next_data_from_html(html)
    assert out == inner


def test_extract_next_data_closing_script_sequence_inside_json_string() -> None:
    """Sequences like </script> inside a JSON string must not truncate parsing."""
    inner = {
        "props": {"pageProps": {"hint": "</script>in_string"}},
        "other": 2,
    }
    blob = json.dumps(inner, separators=(",", ":"))
    html = (
        "<html><script "
        'type="application/json" '
        'id="__NEXT_DATA__">'
        f"{blob}"
        "</script></html>"
    )
    out = extract_next_data_from_html(html)
    assert out == inner


def test_extract_next_data_type_attr_first() -> None:
    inner = {"props": {}, "a": 1}
    blob = json.dumps(inner)
    html = f'<script type="application/json" id=\'__NEXT_DATA__\'>{blob}</script>'
    assert extract_next_data_from_html(html) == inner


def test_extract_next_data_missing_returns_none() -> None:
    assert extract_next_data_from_html("<html><body></body></html>") is None
