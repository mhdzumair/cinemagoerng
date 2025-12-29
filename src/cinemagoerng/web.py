# Copyright 2024-2025 H. Turgut Uyar <uyar@tekir.org>
#
# This file is part of CinemagoerNG.
#
# CinemagoerNG is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# CinemagoerNG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CinemagoerNG.  If not, see <https://www.gnu.org/licenses/>.

import json
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache, partial
from pathlib import Path
from typing import Any, Mapping, NotRequired, TypedDict
from urllib.parse import urlencode

import httpx

from . import model, piculet, registry


_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Firefox/102.0"
_DEFAULT_TIMEOUT = 30.0


class HTTPClient:
    """HTTP client with sync and async support."""

    def __init__(
        self,
        timeout: float = _DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
    ):
        self.timeout = timeout
        self.headers = {"User-Agent": _USER_AGENT}
        if headers:
            self.headers.update(headers)

    def _get_headers(self, url: str, extra: dict[str, str] | None) -> dict:
        headers = self.headers.copy()
        if extra:
            headers.update(extra)
        if "graphql" in url:
            headers["Content-Type"] = "application/json"
        return headers

    def fetch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Fetch URL synchronously."""
        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            response = client.get(url, headers=self._get_headers(url, headers))
            response.raise_for_status()
            return response.text

    async def fetch_async(
        self,
        url: str,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Fetch URL asynchronously."""
        async with httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
        ) as client:
            response = await client.get(
                url, headers=self._get_headers(url, headers)
            )
            response.raise_for_status()
            return response.text


_http_client = HTTPClient()


class GraphQLVariables(TypedDict):
    after: NotRequired[str]
    const: NotRequired[str]
    first: NotRequired[int]
    isAutoTranslationEnabled: NotRequired[bool]
    locale: NotRequired[str]
    originalTitleText: NotRequired[bool]


class GraphQLParams(TypedDict):
    operationName: str
    variables: GraphQLVariables
    extensions: dict[str, Any]


deserialize: partial[Any] = partial(
    piculet.deserialize,
    strconstructed={Decimal}
)


@dataclass(kw_only=True)
class Spec(piculet.Spec):
    version: str
    url: str
    graphql: GraphQLParams | None = None
    doctype: piculet.DocType


SPECS_DIR = Path(__file__).parent / "specs"


@lru_cache(maxsize=None)
def _spec(page: str, /) -> Spec:
    path = SPECS_DIR / f"{page}.json"
    content = path.read_text(encoding="utf-8")
    return piculet.load_spec(
        json.loads(content),
        type_=Spec,
        preprocessors=registry.preprocessors,
        postprocessors=registry.postprocessors,
        transformers=registry.transformers,
    )  # type: ignore


def _get_url(spec: Spec, context: Mapping[str, Any]) -> str:
    url_template = spec.url
    if spec.graphql is not None:
        g_params = []
        for g_key, g_value in spec.graphql.items():
            match g_value:
                case dict():
                    g_dump = json.dumps(g_value, separators=(",", ":"))
                    g_params.append(f"{g_key}={g_dump}")
                case _:
                    g_params.append(f"{g_key}={g_value}")
        url_template += "?" + "&".join(g_params)
    return url_template % context


def _scrape(
        spec: Spec,
        *,
        context: Mapping[str, Any],
        headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    url = _get_url(spec, context=context)
    request_headers = headers if headers is not None else {}
    if spec.graphql is not None:
        request_headers["Content-Type"] = "application/json"
    document = _http_client.fetch(url, headers=request_headers)
    return spec.scrape(document, doctype=spec.doctype)


async def _scrape_async(
        spec: Spec,
        *,
        context: Mapping[str, Any],
        headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    url = _get_url(spec, context=context)
    request_headers = headers if headers is not None else {}
    if spec.graphql is not None:
        request_headers["Content-Type"] = "application/json"
    document = await _http_client.fetch_async(url, headers=request_headers)
    return spec.scrape(document, doctype=spec.doctype)


# =========================================================================
# GET TITLE
# =========================================================================


def get_title(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
) -> model.Title:
    """Get title information synchronously."""
    spec = _spec("title_reference")
    context = {"imdb_id": imdb_id}
    data = _scrape(spec=spec, context=context, headers=headers)
    return deserialize(data, model.Title)


async def get_title_async(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
) -> model.Title:
    """Get title information asynchronously."""
    spec = _spec("title_reference")
    context = {"imdb_id": imdb_id}
    data = await _scrape_async(spec=spec, context=context, headers=headers)
    return deserialize(data, model.Title)


# =========================================================================
# SET TAGLINES
# =========================================================================


def set_taglines(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
) -> None:
    """Update title with taglines synchronously."""
    spec = _spec("title_taglines")
    context = {"imdb_id": title.imdb_id}
    data = _scrape(spec=spec, context=context, headers=headers)
    taglines = data.get("taglines")
    if taglines is not None:
        title.taglines = data["taglines"]


async def set_taglines_async(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
) -> None:
    """Update title with taglines asynchronously."""
    spec = _spec("title_taglines")
    context = {"imdb_id": title.imdb_id}
    data = await _scrape_async(spec=spec, context=context, headers=headers)
    taglines = data.get("taglines")
    if taglines is not None:
        title.taglines = data["taglines"]


# =========================================================================
# SET AKAS
# =========================================================================


def set_akas(
        title: model.Title,
        *,
        spec: Spec | None = None,
        headers: dict[str, str] | None = None,
) -> None:
    """Update title with AKAs (alternative titles) synchronously."""
    if spec is None:
        spec = _spec("title_akas")
    g_params = spec.graphql
    assert g_params is not None, g_params
    g_vars = g_params["variables"]
    context: dict[str, Any] = {"imdb_id": title.imdb_id} | g_vars
    data = _scrape(spec, context=context, headers=headers)
    akas = [deserialize(aka, model.AKA) for aka in data.get("akas", [])]
    title.akas.extend(akas)
    if data.get("has_next_page", False):
        g_vars["after"] = data["end_cursor"]
        set_akas(title, spec=spec, headers=headers)


async def set_akas_async(
        title: model.Title,
        *,
        spec: Spec | None = None,
        headers: dict[str, str] | None = None,
) -> None:
    """Update title with AKAs (alternative titles) asynchronously."""
    if spec is None:
        spec = _spec("title_akas")
    g_params = spec.graphql
    assert g_params is not None, g_params
    g_vars = g_params["variables"]
    context: dict[str, Any] = {"imdb_id": title.imdb_id} | g_vars
    data = await _scrape_async(spec, context=context, headers=headers)
    akas = [deserialize(aka, model.AKA) for aka in data.get("akas", [])]
    title.akas.extend(akas)
    if data.get("has_next_page", False):
        g_vars["after"] = data["end_cursor"]
        await set_akas_async(title, spec=spec, headers=headers)


# =========================================================================
# SET PARENTAL GUIDE
# =========================================================================


def set_parental_guide(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
) -> None:
    """Update title with parental guide information synchronously."""
    spec = _spec("title_parental_guide")
    context = {"imdb_id": title.imdb_id}
    data = _scrape(spec=spec, context=context, headers=headers)
    title.certification = deserialize(
        data["certification"],
        model.Certification,
    )
    title.advisories = deserialize(data["advisories"], model.Advisories)


async def set_parental_guide_async(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
) -> None:
    """Update title with parental guide information asynchronously."""
    spec = _spec("title_parental_guide")
    context = {"imdb_id": title.imdb_id}
    data = await _scrape_async(spec=spec, context=context, headers=headers)
    title.certification = deserialize(
        data["certification"],
        model.Certification,
    )
    title.advisories = deserialize(data["advisories"], model.Advisories)


# =========================================================================
# SET EPISODES
# =========================================================================


def set_episodes(
        title: model.TVSeries | model.TVMiniSeries,
        *,
        season: str,
        headers: dict[str, str] | None = None,
) -> None:
    """Update TV series with episodes for a season synchronously."""
    spec = _spec("title_episodes")
    context = {"imdb_id": title.imdb_id, "season": season}
    data = _scrape(spec=spec, context=context, headers=headers)
    episodes = data.get("episodes")
    if episodes is not None:
        title.episodes[season] = deserialize(
            episodes,
            dict[str, model.TVEpisode],
        )


async def set_episodes_async(
        title: model.TVSeries | model.TVMiniSeries,
        *,
        season: str,
        headers: dict[str, str] | None = None,
) -> None:
    """Update TV series with episodes for a season asynchronously."""
    spec = _spec("title_episodes")
    context = {"imdb_id": title.imdb_id, "season": season}
    data = await _scrape_async(spec=spec, context=context, headers=headers)
    episodes = data.get("episodes")
    if episodes is not None:
        title.episodes[season] = deserialize(
            episodes,
            dict[str, model.TVEpisode],
        )


# =========================================================================
# SEARCH TITLES
# =========================================================================


def _parse_search_results(results: list[dict]) -> list[model.Title]:
    """Parse search results into Title objects."""
    from typedload.exceptions import TypedloadValueError

    titles = []
    for result in results:
        try:
            title = deserialize(result, model.Title)
            titles.append(title)
        except TypedloadValueError:
            continue
    return titles


def _build_search_url(
    spec: Spec,
    query: str,
    filters: model.SearchFilters | None,
    sort: model.SortCriteria,
    count: int,
) -> str:
    """Build search URL with parameters."""
    params: dict[str, Any] = {
        "title": query,
        "count": count,
        "sort": sort.to_url_param(),
    }
    if filters:
        params.update(filters.to_url_params())
    url_params = urlencode(params)
    return spec.url % {"url_params": url_params}


def _prepare_graphql_pagination(
    data: dict,
    query: str,
    filters: model.SearchFilters | None,
    sort: model.SortCriteria,
    count: int,
) -> dict[str, Any]:
    """Prepare variables for GraphQL pagination query."""
    variables: dict[str, Any] = {
        "after": data.get("end_cursor"),
        "first": count,
        "locale": "en-US",
        "titleTextConstraint": {"searchTerm": query},
    }

    if filters:
        variables.update(filters.to_graphql_variables())

    sort_field, sort_order = sort.to_graphql_params()
    variables["sortBy"] = sort_field
    variables["sortOrder"] = sort_order

    return variables


def _build_pagination_url(spec: Spec, graphql_vars: dict[str, Any]) -> str:
    """Build GraphQL pagination URL."""
    extensions = {
        "persistedQuery": {
            "sha256Hash": (
                "60a7b8470b01671336ffa535b21a0a6cdaf50267fa2ab55b3e3772578a8c1f00"
            ),
            "version": 1,
        }
    }
    variables_json = json.dumps(graphql_vars, separators=(",", ":"))
    extensions_json = json.dumps(extensions, separators=(",", ":"))
    return spec.url % {
        "variables": variables_json,
        "extensions": extensions_json,
    }


def search_titles(
    query: str = "",
    *,
    filters: model.SearchFilters | None = None,
    sort: model.SortCriteria = model.SortCriteria(model.SortField.POPULARITY),
    count: int = 50,
    total_count: int | None = 250,
    paginate: bool = False,
    headers: dict[str, str] | None = None,
) -> list[model.Title]:
    """
    Search for titles on IMDb with advanced filtering options.

    Args:
        query: Search query string
        filters: Search filters including title types, genres, etc.
        sort: Sort criteria for results
        count: Maximum number of items to fetch per request (max 100)
        total_count: Total number of items to fetch (when paginate=True)
        paginate: Whether to fetch all pages of results
        headers: Optional HTTP headers

    Returns:
        List of Title objects
    """
    spec = _spec("title_search")
    count = min(count, 100)

    url = _build_search_url(spec, query, filters, sort, count)
    document = _http_client.fetch(url, headers=headers)
    data = spec.scrape(document, doctype=spec.doctype)

    titles = _parse_search_results(data.get("results", []))

    if not paginate:
        return titles

    # Check if there are more results
    total_results = data.get("total_results", 0)
    has_next_page = len(data.get("results", [])) < total_results

    if not has_next_page:
        return titles

    # Continue with GraphQL pagination
    pagination_spec = _spec("title_search_with_pagination")
    graphql_vars = _prepare_graphql_pagination(
        data, query, filters, sort, count
    )

    while has_next_page and (
        total_count is None or len(titles) < total_count
    ):
        url = _build_pagination_url(pagination_spec, graphql_vars)
        document = _http_client.fetch(url, headers=headers)
        page_data = pagination_spec.scrape(
            document, doctype=pagination_spec.doctype
        )

        new_titles = _parse_search_results(page_data.get("results", []))
        titles.extend(new_titles)

        has_next_page = page_data.get("has_next_page", False)
        if has_next_page:
            graphql_vars["after"] = page_data.get("end_cursor")

    return titles


async def search_titles_async(
    query: str = "",
    *,
    filters: model.SearchFilters | None = None,
    sort: model.SortCriteria = model.SortCriteria(model.SortField.POPULARITY),
    count: int = 50,
    total_count: int | None = 250,
    paginate: bool = False,
    headers: dict[str, str] | None = None,
) -> list[model.Title]:
    """
    Search for titles on IMDb asynchronously with advanced filtering options.

    Args:
        query: Search query string
        filters: Search filters including title types, genres, etc.
        sort: Sort criteria for results
        count: Maximum number of items to fetch per request (max 100)
        total_count: Total number of items to fetch (when paginate=True)
        paginate: Whether to fetch all pages of results
        headers: Optional HTTP headers

    Returns:
        List of Title objects
    """
    spec = _spec("title_search")
    count = min(count, 100)

    url = _build_search_url(spec, query, filters, sort, count)
    document = await _http_client.fetch_async(url, headers=headers)
    data = spec.scrape(document, doctype=spec.doctype)

    titles = _parse_search_results(data.get("results", []))

    if not paginate:
        return titles

    # Check if there are more results
    total_results = data.get("total_results", 0)
    has_next_page = len(data.get("results", [])) < total_results

    if not has_next_page:
        return titles

    # Continue with GraphQL pagination
    pagination_spec = _spec("title_search_with_pagination")
    graphql_vars = _prepare_graphql_pagination(
        data, query, filters, sort, count
    )

    while has_next_page and (
        total_count is None or len(titles) < total_count
    ):
        url = _build_pagination_url(pagination_spec, graphql_vars)
        document = await _http_client.fetch_async(url, headers=headers)
        page_data = pagination_spec.scrape(
            document, doctype=pagination_spec.doctype
        )

        new_titles = _parse_search_results(page_data.get("results", []))
        titles.extend(new_titles)

        has_next_page = page_data.get("has_next_page", False)
        if has_next_page:
            graphql_vars["after"] = page_data.get("end_cursor")

    return titles
