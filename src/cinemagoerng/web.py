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
        httpx_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """Fetch URL synchronously."""
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "follow_redirects": True,
        }
        if httpx_kwargs:
            kwargs.update(httpx_kwargs)
        with httpx.Client(**kwargs) as client:
            response = client.get(url, headers=self._get_headers(url, headers))
            response.raise_for_status()
            return response.text

    async def fetch_async(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """Fetch URL asynchronously."""
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "follow_redirects": True,
        }
        if httpx_kwargs:
            kwargs.update(httpx_kwargs)
        async with httpx.AsyncClient(**kwargs) as client:
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
        httpx_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = _get_url(spec, context=context)
    request_headers = headers if headers is not None else {}
    if spec.graphql is not None:
        request_headers["Content-Type"] = "application/json"
    document = _http_client.fetch(
        url, headers=request_headers, httpx_kwargs=httpx_kwargs
    )
    return spec.scrape(document, doctype=spec.doctype)


async def _scrape_async(
        spec: Spec,
        *,
        context: Mapping[str, Any],
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = _get_url(spec, context=context)
    request_headers = headers if headers is not None else {}
    if spec.graphql is not None:
        request_headers["Content-Type"] = "application/json"
    document = await _http_client.fetch_async(
        url, headers=request_headers, httpx_kwargs=httpx_kwargs
    )
    return spec.scrape(document, doctype=spec.doctype)


# =========================================================================
# GET TITLE
# =========================================================================


def get_title(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title:
    """Get title information synchronously."""
    spec = _spec("title_reference")
    context = {"imdb_id": imdb_id}
    data = _scrape(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
    return deserialize(data, model.Title)


async def get_title_async(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title:
    """Get title information asynchronously."""
    spec = _spec("title_reference")
    context = {"imdb_id": imdb_id}
    data = await _scrape_async(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
    return deserialize(data, model.Title)


# =========================================================================
# SET TAGLINES
# =========================================================================


def set_taglines(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update title with taglines synchronously."""
    spec = _spec("title_taglines")
    context = {"imdb_id": title.imdb_id}
    data = _scrape(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
    taglines = data.get("taglines")
    if taglines is not None:
        title.taglines = data["taglines"]


async def set_taglines_async(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update title with taglines asynchronously."""
    spec = _spec("title_taglines")
    context = {"imdb_id": title.imdb_id}
    data = await _scrape_async(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
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
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update title with AKAs (alternative titles) synchronously."""
    if spec is None:
        spec = _spec("title_akas")
    g_params = spec.graphql
    assert g_params is not None, g_params
    g_vars = g_params["variables"]
    context: dict[str, Any] = {"imdb_id": title.imdb_id} | g_vars
    data = _scrape(spec, context=context, headers=headers,
                   httpx_kwargs=httpx_kwargs)
    akas = [deserialize(aka, model.AKA) for aka in data.get("akas", [])]
    title.akas.extend(akas)
    if data.get("has_next_page", False):
        g_vars["after"] = data["end_cursor"]
        set_akas(title, spec=spec, headers=headers, httpx_kwargs=httpx_kwargs)


async def set_akas_async(
        title: model.Title,
        *,
        spec: Spec | None = None,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update title with AKAs (alternative titles) asynchronously."""
    if spec is None:
        spec = _spec("title_akas")
    g_params = spec.graphql
    assert g_params is not None, g_params
    g_vars = g_params["variables"]
    context: dict[str, Any] = {"imdb_id": title.imdb_id} | g_vars
    data = await _scrape_async(spec, context=context, headers=headers,
                               httpx_kwargs=httpx_kwargs)
    akas = [deserialize(aka, model.AKA) for aka in data.get("akas", [])]
    title.akas.extend(akas)
    if data.get("has_next_page", False):
        g_vars["after"] = data["end_cursor"]
        await set_akas_async(
            title, spec=spec, headers=headers, httpx_kwargs=httpx_kwargs
        )


# =========================================================================
# SET PARENTAL GUIDE
# =========================================================================


def set_parental_guide(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update title with parental guide information synchronously."""
    spec = _spec("title_parental_guide")
    context = {"imdb_id": title.imdb_id}
    data = _scrape(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
    title.certification = deserialize(
        data["certification"],
        model.Certification,
    )
    title.advisories = deserialize(data["advisories"], model.Advisories)


async def set_parental_guide_async(
        title: model.Title,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update title with parental guide information asynchronously."""
    spec = _spec("title_parental_guide")
    context = {"imdb_id": title.imdb_id}
    data = await _scrape_async(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
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
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update TV series with episodes for a season synchronously."""
    spec = _spec("title_episodes")
    context = {"imdb_id": title.imdb_id, "season": season}
    data = _scrape(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
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
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """Update TV series with episodes for a season asynchronously."""
    spec = _spec("title_episodes")
    context = {"imdb_id": title.imdb_id, "season": season}
    data = await _scrape_async(
        spec=spec, context=context, headers=headers, httpx_kwargs=httpx_kwargs
    )
    episodes = data.get("episodes")
    if episodes is not None:
        title.episodes[season] = deserialize(
            episodes,
            dict[str, model.TVEpisode],
        )


# =========================================================================
# SET ALL EPISODES (GRAPHQL PAGINATION)
# =========================================================================

_EPISODES_GRAPHQL_HASH = (
    "e5b755e1254e3bc3a36b34aff729b1d107a63263dec628a8f59935c9e778c70e"
)


def _build_episodes_graphql_url(
    imdb_id: str,
    after: str = "",
    first: int = 250,
    *,
    seasons: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> str:
    """
    Build GraphQL URL for fetching episodes with pagination.

    Args:
        imdb_id: The IMDb ID of the TV series
        after: Cursor for pagination (empty string for first page)
        first: Number of episodes per page (max 250)
        seasons: Optional list of season numbers to filter by
        year_from: Optional start year for filtering episodes
        year_to: Optional end year for filtering episodes
    """
    from urllib.parse import quote

    variables: dict[str, Any] = {
        "after": after,
        "const": imdb_id,
        "first": first,
        "locale": "en-US",
        "originalTitleText": False,
        "returnUrl": "https://www.imdb.com/close_me",
        "sort": {"by": "EPISODE_THEN_RELEASE", "order": "ASC"},
    }

    # Add filter if seasons or year range specified
    if seasons is not None:
        variables["filter"] = {"includeSeasons": seasons}
    elif year_from is not None or year_to is not None:
        filter_dict: dict[str, Any] = {}
        if year_from is not None:
            filter_dict["releasedOnOrAfter"] = {"year": year_from}
        if year_to is not None:
            filter_dict["releasedOnOrBefore"] = {"year": year_to}
        variables["filter"] = filter_dict

    extensions = {
        "persistedQuery": {
            "sha256Hash": _EPISODES_GRAPHQL_HASH,
            "version": 1,
        }
    }
    variables_json = quote(json.dumps(variables, separators=(",", ":")))
    extensions_json = quote(json.dumps(extensions, separators=(",", ":")))
    base_url = "https://caching.graphql.imdb.com/"
    return (
        f"{base_url}?operationName=TitleEpisodesSubPagePagination"
        f"&variables={variables_json}&extensions={extensions_json}"
    )


def _add_episodes_from_data(
    title: model.TVSeries | model.TVMiniSeries,
    episodes_data: list[dict[str, Any]],
) -> None:
    """Add episodes from scraped data to title, avoiding duplicates."""
    for ep_data in episodes_data:
        episode = deserialize(ep_data, model.TVEpisode)
        season_key = str(ep_data.get("season", "unknown"))
        ep_num = str(ep_data.get("episode", "unknown"))

        if season_key not in title.episodes:
            title.episodes[season_key] = {}

        # Only add if not already present (avoid duplicates)
        if ep_num not in title.episodes[season_key]:
            title.episodes[season_key][ep_num] = episode


def set_all_episodes(
        title: model.TVSeries | model.TVMiniSeries,
        *,
        seasons: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """
    Fetch all episodes for a TV series using GraphQL pagination.

    This fetches episodes efficiently using paginated GraphQL requests.

    Args:
        title: The TV series to update with episodes
        seasons: Optional list of season numbers to filter (e.g., ["1", "2"])
        year_from: Optional start year to filter episodes
        year_to: Optional end year to filter episodes
        headers: Optional HTTP headers
        httpx_kwargs: Optional httpx client kwargs (e.g., {"proxy": "..."})
    """
    spec = _spec("title_episodes_with_pagination")
    after = ""

    while True:
        url = _build_episodes_graphql_url(
            title.imdb_id,
            after=after,
            seasons=seasons,
            year_from=year_from,
            year_to=year_to,
        )
        document = _http_client.fetch(
            url, headers=headers, httpx_kwargs=httpx_kwargs
        )
        data = spec.scrape(document, doctype=spec.doctype)

        _add_episodes_from_data(title, data.get("episodes", []))

        if not data.get("has_next_page", False):
            break
        after = data.get("end_cursor", "")


async def set_all_episodes_async(
        title: model.TVSeries | model.TVMiniSeries,
        *,
        seasons: list[str] | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> None:
    """
    Fetch all episodes for a TV series using GraphQL pagination asynchronously.

    This fetches episodes efficiently using paginated GraphQL requests.

    Args:
        title: The TV series to update with episodes
        seasons: Optional list of season numbers to filter (e.g., ["1", "2"])
        year_from: Optional start year to filter episodes
        year_to: Optional end year to filter episodes
        headers: Optional HTTP headers
        httpx_kwargs: Optional httpx client kwargs (e.g., {"proxy": "..."})
    """
    spec = _spec("title_episodes_with_pagination")
    after = ""

    while True:
        url = _build_episodes_graphql_url(
            title.imdb_id,
            after=after,
            seasons=seasons,
            year_from=year_from,
            year_to=year_to,
        )
        document = await _http_client.fetch_async(
            url, headers=headers, httpx_kwargs=httpx_kwargs
        )
        data = spec.scrape(document, doctype=spec.doctype)

        _add_episodes_from_data(title, data.get("episodes", []))

        if not data.get("has_next_page", False):
            break
        after = data.get("end_cursor", "")


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
    httpx_kwargs: dict[str, Any] | None = None,
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
        httpx_kwargs: Optional httpx client kwargs (e.g., {"proxy": "..."})

    Returns:
        List of Title objects
    """
    spec = _spec("title_search")
    count = min(count, 100)

    url = _build_search_url(spec, query, filters, sort, count)
    document = _http_client.fetch(url, headers=headers,
                                  httpx_kwargs=httpx_kwargs)
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
        document = _http_client.fetch(url, headers=headers,
                                      httpx_kwargs=httpx_kwargs)
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
    httpx_kwargs: dict[str, Any] | None = None,
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
        httpx_kwargs: Optional httpx client kwargs (e.g., {"proxy": "..."})

    Returns:
        List of Title objects
    """
    spec = _spec("title_search")
    count = min(count, 100)

    url = _build_search_url(spec, query, filters, sort, count)
    document = await _http_client.fetch_async(url, headers=headers,
                                              httpx_kwargs=httpx_kwargs)
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
        document = await _http_client.fetch_async(url, headers=headers,
                                                  httpx_kwargs=httpx_kwargs)
        page_data = pagination_spec.scrape(
            document, doctype=pagination_spec.doctype
        )

        new_titles = _parse_search_results(page_data.get("results", []))
        titles.extend(new_titles)

        has_next_page = page_data.get("has_next_page", False)
        if has_next_page:
            graphql_vars["after"] = page_data.get("end_cursor")

    return titles
