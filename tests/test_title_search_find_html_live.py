"""Optional live check: /find/ HTML + ``__NEXT_DATA__`` (title search fallback path)."""

import pytest
from curl_cffi import requests as cr

from cinemagoerng.web import _build_search_url, _search_titles_via_html, _spec

_IMDB_FIND_HEADERS = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.imdb.com/",
    "Upgrade-Insecure-Requests": "1",
}


def _find_page_has_next_data(query: str) -> bool:
    spec = _spec("title_search")
    url = _build_search_url(spec, query)
    response = cr.get(
        url,
        impersonate="chrome131",
        timeout=60,
        headers=_IMDB_FIND_HEADERS,
    )
    return response.status_code == 200 and "__NEXT_DATA__" in response.text


@pytest.mark.integration
def test_search_titles_via_html_parses_find_page(
    imdb_uncached_fetch: None,
) -> None:
    """Resolves titles from ``/find/`` when IMDb returns real HTML (not WAF)."""
    if not _find_page_has_next_data("The Matrix"):
        pytest.skip(
            "IMDb /find/ did not return __NEXT_DATA__ (WAF, block, or non-200)."
        )
    titles = _search_titles_via_html("The Matrix", None, None)
    ids = {t.imdb_id for t in titles}
    assert "tt0133093" in ids
