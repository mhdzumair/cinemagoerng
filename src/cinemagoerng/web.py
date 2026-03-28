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

import asyncio
import json
from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache, partial
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping, NotRequired, TypedDict
from urllib.parse import quote, urlencode

from curl_cffi import requests as curl_requests
from curl_cffi.requests import AsyncSession

from . import model, piculet, registry


# Browser-like defaults reduce empty 202 responses on www.imdb.com HTML.
_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_DEFAULT_TIMEOUT = 30.0
# TLS/JA3 fingerprint impersonation (see curl_cffi docs for other targets).
_CURL_IMPERSONATE = "chrome131"
# Extra profiles to try on www.imdb.com HTML when the first impersonate fails
# validation (empty body / WAF). Set to () to disable. Order: user override,
# then this chain (deduplicated).
_IMDB_IMPERSONATE_FALLBACKS: tuple[str, ...] = (
    "chrome131",
    "chrome124",
    "chrome120",
    "chrome110",
    "safari17_0",
    "safari15_5",
)
_SUGGESTION_BASE_URL = "https://v3.sg.media-imdb.com/suggestion"

# (url, merged_request_headers, per_request_extra) -> response body text.
HTTPFetchCallable = Callable[
    [str, dict[str, str], dict[str, Any] | None],
    str,
]
HTTPFetchAsyncCallable = Callable[
    [str, dict[str, str], dict[str, Any] | None],
    Awaitable[str],
]

_IMDB_WWW_HTML_DEFAULT_HEADERS: dict[str, str] = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

# caching.graphql.imdb.com may return Midway auth HTML if these are missing.
_IMDB_GRAPHQL_DEFAULT_HEADERS: dict[str, str] = {
    "Accept": "application/graphql+json, application/json;q=0.9, */*;q=0.8",
    "Referer": "https://www.imdb.com/",
    "Origin": "https://www.imdb.com",
}

_SUGGESTION_TYPE_MAP = {
    "feature": "movie",
    "movie": "movie",
    "tv movie": "tvMovie",
    "video": "video",
    "video game": "videoGame",
    "short": "short",
    "tv short": "tvShort",
    "tv series": "tvSeries",
    "tv mini series": "tvMiniSeries",
    "tv mini-series": "tvMiniSeries",
    "tv episode": "tvEpisode",
    "tv special": "tvSpecial",
    "music video": "musicVideo",
    "podcast series": "podcastSeries",
    "podcast episode": "podcastEpisode",
}


def _is_imdb_www_html_url(url: str) -> bool:
    """IMDb title/tag HTML on www; not GraphQL or suggestion JSON hosts."""
    return "www.imdb.com" in url and "graphql" not in url


def _validate_imdb_www_html_response(url: str, text: str) -> None:
    """
    Raise a clear error when IMDb blocks automation (empty body or WAF page).

    Browsers still work because of TLS fingerprinting, cookies, and
    residential IPs; datacenter scrapers often get empty 202 bodies or a WAF
    challenge page.
    """
    if not _is_imdb_www_html_url(url):
        return
    # /find/ search HTML is best-effort; WAF is common — let the parser fail
    # downstream instead of aborting before scrape.
    if "/find/" in url:
        return
    if not text or not text.strip():
        raise RuntimeError(
            "IMDb returned an empty response body for "
            f"{url!r}. This usually means the request was blocked as a bot "
            "(common from datacenter IPs). If the title opens in a browser, "
            "try a residential proxy, browser cookies, or pass custom headers "
            "via get_title(..., headers=...) / httpx_kwargs (curl_cffi)."
        )
    if "gokuProps" in text and "__NEXT_DATA__" not in text:
        raise RuntimeError(
            "IMDb returned an AWS WAF challenge page instead of real HTML for "
            f"{url!r}. Plain HTTP clients cannot pass this; use a browser "
            "session (cookies), a proxy, or an undetected/automation stack."
        )


class HTTPClient:
    """HTTP client (curl_cffi): browser TLS + optional impersonation retries.

    When IMDb returns an empty body or WAF HTML on www.imdb.com title/tag
    pages, the client retries the same URL with additional ``impersonate``
    targets (see ``_IMDB_IMPERSONATE_FALLBACKS``). That does not replace a
    residential IP or cookies, but it often helps when one fingerprint is
    blocked.

    For Playwright or other automation, pass ``fetch_impl`` (sync) and
    optionally ``fetch_async_impl`` (async). Hooks receive the final merged
    ``headers`` and the same ``httpx_kwargs`` dict passed into ``get_title`` /
    ``search_titles`` (e.g. ``proxy`` / curl_cffi options). Install app-wide
    with :func:`set_default_http_client`.

    Other effective approaches (caller supplies via ``headers`` /
    ``httpx_kwargs``): ``Cookie`` from a real session, ``proxies`` (curl_cffi
    accepts the same style as Requests), or a wrapper that drives Playwright
    and returns HTML strings.
    """

    def __init__(
        self,
        timeout: float = _DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        *,
        fetch_impl: HTTPFetchCallable | None = None,
        fetch_async_impl: HTTPFetchAsyncCallable | None = None,
    ):
        self.timeout = timeout
        self.headers = {"User-Agent": _USER_AGENT}
        if headers:
            self.headers.update(headers)
        self._fetch_impl = fetch_impl
        self._fetch_async_impl = fetch_async_impl

    def _get_headers(self, url: str, extra: dict[str, str] | None) -> dict:
        headers = self.headers.copy()
        if extra:
            headers.update(extra)
        if _is_imdb_www_html_url(url):
            for key, value in _IMDB_WWW_HTML_DEFAULT_HEADERS.items():
                headers.setdefault(key, value)
        if "graphql" in url:
            for key, value in _IMDB_GRAPHQL_DEFAULT_HEADERS.items():
                headers.setdefault(key, value)
            headers.setdefault("Content-Type", "application/json")
        return headers

    def _curl_request_kwargs(
        self,
        httpx_kwargs: dict[str, Any] | None,
    ) -> tuple[dict[str, Any], str]:
        """Build per-request kwargs and primary impersonate (httpx-compat)."""
        merged: dict[str, Any] = dict(httpx_kwargs) if httpx_kwargs else {}
        impersonate = merged.pop("impersonate", _CURL_IMPERSONATE)
        req_kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "allow_redirects": True,
        }
        req_kwargs.update(merged)
        if "follow_redirects" in req_kwargs:
            req_kwargs["allow_redirects"] = req_kwargs.pop(
                "follow_redirects"
            )
        return req_kwargs, impersonate

    @staticmethod
    def _impersonate_chain(primary: str) -> list[str]:
        return list(
            dict.fromkeys((primary, *_IMDB_IMPERSONATE_FALLBACKS))
        )

    def fetch(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """Fetch URL synchronously."""
        merged_headers = self._get_headers(url, headers)
        if self._fetch_impl is not None:
            text = self._fetch_impl(url, merged_headers, httpx_kwargs)
            _validate_imdb_www_html_response(url, text)
            return text

        req_kwargs, primary_imp = self._curl_request_kwargs(httpx_kwargs)
        last_exc: BaseException | None = None
        for imp in self._impersonate_chain(primary_imp):
            try:
                response = curl_requests.get(
                    url,
                    headers=merged_headers,
                    impersonate=imp,
                    **req_kwargs,
                )
                response.raise_for_status()
                text = response.text
                try:
                    _validate_imdb_www_html_response(url, text)
                except RuntimeError as exc:
                    last_exc = exc
                    continue
                return text
            except curl_requests.exceptions.RequestException as exc:
                last_exc = exc
                continue
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"IMDb fetch failed for {url!r} after retries.")

    async def fetch_async(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
    ) -> str:
        """Fetch URL asynchronously."""
        merged_headers = self._get_headers(url, headers)
        if self._fetch_async_impl is not None:
            text = await self._fetch_async_impl(
                url, merged_headers, httpx_kwargs
            )
            _validate_imdb_www_html_response(url, text)
            return text
        if self._fetch_impl is not None:
            text = await asyncio.to_thread(
                self._fetch_impl,
                url,
                merged_headers,
                httpx_kwargs,
            )
            _validate_imdb_www_html_response(url, text)
            return text

        req_kwargs, primary_imp = self._curl_request_kwargs(httpx_kwargs)
        last_exc: BaseException | None = None
        async with AsyncSession() as session:
            for imp in self._impersonate_chain(primary_imp):
                try:
                    response = await session.get(
                        url,
                        headers=merged_headers,
                        impersonate=imp,
                        **req_kwargs,
                    )
                    response.raise_for_status()
                    text = response.text
                    try:
                        _validate_imdb_www_html_response(url, text)
                    except RuntimeError as exc:
                        last_exc = exc
                        continue
                    return text
                except curl_requests.exceptions.RequestException as exc:
                    last_exc = exc
                    continue
        if last_exc is not None:
            raise last_exc
        raise RuntimeError(f"IMDb fetch failed for {url!r} after retries.")


_http_client = HTTPClient()


def set_default_http_client(client: HTTPClient) -> None:
    """Use *client* for all library HTTP (get_title, search, GraphQL, …)."""
    global _http_client
    _http_client = client


class GraphQLVariables(TypedDict):
    after: NotRequired[str]
    const: NotRequired[str]
    first: NotRequired[int]
    isAutoTranslationEnabled: NotRequired[bool]
    isInMachineTranslateWeblab: NotRequired[bool]
    locale: NotRequired[str]
    originalTitleText: NotRequired[bool]
    pageConst: NotRequired[str]
    titleId: NotRequired[str]


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

    def scrape(
        self,
        document: str | piculet.Node,
        *,
        doctype: piculet.DocType,
    ) -> dict[str, Any]:
        """
        Scrape via Piculet; read IMDb __NEXT_DATA__ JSON from raw HTML first.
        """
        if (
            isinstance(document, str)
            and doctype == "html"
            and self.pre == ["parse_next_data"]
        ):
            extracted_pre = registry.extract_next_data_from_html(document)
            if extracted_pre is not None:
                data = self.extract(extracted_pre)
                return self.postprocess(data)
        return super().scrape(document, doctype=doctype)


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
        pairs: list[tuple[str, str]] = []
        for g_key, g_value in spec.graphql.items():
            match g_value:
                case dict():
                    dumped = json.dumps(g_value, separators=(",", ":"))
                    fragment = dumped % context
                case _:
                    fragment = str(g_value)
                    if "%(" in fragment:
                        fragment = fragment % context
            pairs.append((g_key, fragment))
        return url_template + "?" + urlencode(pairs)
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


# HTML specs tried in order for get_title / get_title_async (reference first).
_TITLE_HTML_SPEC_ORDER: tuple[str, ...] = ("title_reference", "title_primary")

_TITLE_GRAPHQL_ALL_TOPICS = "title_graphql_all_topics"
_TITLE_GRAPHQL_STORYLINE = "title_graphql_storyline"


def _merge_graphql_title_scrape_parts(
        *parts: dict[str, Any],
) -> dict[str, Any]:
    """Merge Piculet scrape dicts; later parts override when non-empty."""
    merged: dict[str, Any] = {}
    for part in parts:
        for key, val in part.items():
            if val is None:
                continue
            if val == [] or val == {}:
                continue
            merged[key] = val
    return merged


def _get_title_from_graphql(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title | None:
    """Build a Title from IMDb caching GraphQL (persisted queries)."""
    context = {"imdb_id": imdb_id}
    try:
        topics = _scrape(
            spec=_spec(_TITLE_GRAPHQL_ALL_TOPICS),
            context=context,
            headers=headers,
            httpx_kwargs=httpx_kwargs,
        )
    except Exception:
        return None
    try:
        storyline = _scrape(
            spec=_spec(_TITLE_GRAPHQL_STORYLINE),
            context=context,
            headers=headers,
            httpx_kwargs=httpx_kwargs,
        )
    except Exception:
        storyline = {}
    merged = _merge_graphql_title_scrape_parts(topics, storyline)
    merged["imdb_id"] = imdb_id.strip()
    try:
        return deserialize(merged, model.Title)
    except Exception:
        return None


async def _get_title_from_graphql_async(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title | None:
    context = {"imdb_id": imdb_id}
    try:
        topics = await _scrape_async(
            spec=_spec(_TITLE_GRAPHQL_ALL_TOPICS),
            context=context,
            headers=headers,
            httpx_kwargs=httpx_kwargs,
        )
    except Exception:
        return None
    try:
        storyline = await _scrape_async(
            spec=_spec(_TITLE_GRAPHQL_STORYLINE),
            context=context,
            headers=headers,
            httpx_kwargs=httpx_kwargs,
        )
    except Exception:
        storyline = {}
    merged = _merge_graphql_title_scrape_parts(topics, storyline)
    merged["imdb_id"] = imdb_id.strip()
    try:
        return deserialize(merged, model.Title)
    except Exception:
        return None


def _title_data_from_suggestion_payload(
        imdb_id: str,
        payload: dict[str, Any],
) -> dict[str, Any] | None:
    """Map suggestion API JSON into a *title_reference*-like scrape dict."""
    items = payload.get("d")
    if not isinstance(items, list):
        return None
    needle = imdb_id.strip()
    for raw in items:
        if not isinstance(raw, dict):
            continue
        rid = raw.get("id")
        if rid != needle:
            continue
        qid = raw.get("qid")
        if not isinstance(qid, str) or not qid:
            return None
        image_block = raw.get("i")
        img_url = None
        if isinstance(image_block, dict):
            img_url = image_block.get("imageUrl")
        y_raw = raw.get("y")
        year: int | None
        if y_raw is None:
            year = None
        else:
            try:
                year = int(y_raw)
            except (TypeError, ValueError):
                year = None
        title_text = raw.get("l")
        return {
            "imdb_id": rid,
            "title": title_text if isinstance(title_text, str) else "",
            "type_id": qid,
            "year": year,
            "primary_image": img_url,
        }
    return None


def _get_title_from_suggestion(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title | None:
    """Minimal title via v3.sg.media-imdb.com suggestion JSON."""
    url = f"{_SUGGESTION_BASE_URL}/x/{quote(imdb_id.strip())}.json"
    try:
        body = _http_client.fetch(
            url, headers=headers or {}, httpx_kwargs=httpx_kwargs
        )
        payload = json.loads(body)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    data = _title_data_from_suggestion_payload(imdb_id, payload)
    if data is None:
        return None
    try:
        return deserialize(data, model.Title)
    except Exception:
        return None


async def _get_title_from_suggestion_async(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title | None:
    url = f"{_SUGGESTION_BASE_URL}/x/{quote(imdb_id.strip())}.json"
    try:
        body = await _http_client.fetch_async(
            url, headers=headers or {}, httpx_kwargs=httpx_kwargs
        )
        payload = json.loads(body)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    data = _title_data_from_suggestion_payload(imdb_id, payload)
    if data is None:
        return None
    try:
        return deserialize(data, model.Title)
    except Exception:
        return None


# =========================================================================
# GET TITLE
# =========================================================================


def get_title(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title:
    """Get title information synchronously.

    Tries ``/title/{id}/reference/`` HTML, then canonical ``/title/{id}/``,
    then IMDb caching GraphQL (``TitleAllTopics`` + ``Title_Storyline``),
    then the suggestion JSON API (minimal cast/plot/credits).
    """
    errors: list[Exception] = []
    context = {"imdb_id": imdb_id}
    for spec_name in _TITLE_HTML_SPEC_ORDER:
        try:
            spec = _spec(spec_name)
            data = _scrape(
                spec=spec,
                context=context,
                headers=headers,
                httpx_kwargs=httpx_kwargs,
            )
            return deserialize(data, model.Title)
        except Exception as exc:
            errors.append(exc)
    gql_title = _get_title_from_graphql(
        imdb_id, headers=headers, httpx_kwargs=httpx_kwargs
    )
    if gql_title is not None:
        return gql_title
    boot = _get_title_from_suggestion(
        imdb_id, headers=headers, httpx_kwargs=httpx_kwargs
    )
    if boot is not None:
        return boot
    if errors:
        raise errors[-1]
    raise RuntimeError(f"IMDb title fetch failed for {imdb_id!r}.")


async def get_title_async(
        imdb_id: str,
        *,
        headers: dict[str, str] | None = None,
        httpx_kwargs: dict[str, Any] | None = None,
) -> model.Title:
    """Get title information asynchronously (see :func:`get_title`)."""
    errors: list[Exception] = []
    context = {"imdb_id": imdb_id}
    for spec_name in _TITLE_HTML_SPEC_ORDER:
        try:
            spec = _spec(spec_name)
            data = await _scrape_async(
                spec=spec,
                context=context,
                headers=headers,
                httpx_kwargs=httpx_kwargs,
            )
            return deserialize(data, model.Title)
        except Exception as exc:
            errors.append(exc)
    gql_title = await _get_title_from_graphql_async(
        imdb_id, headers=headers, httpx_kwargs=httpx_kwargs
    )
    if gql_title is not None:
        return gql_title
    boot = await _get_title_from_suggestion_async(
        imdb_id, headers=headers, httpx_kwargs=httpx_kwargs
    )
    if boot is not None:
        return boot
    if errors:
        raise errors[-1]
    raise RuntimeError(f"IMDb title fetch failed for {imdb_id!r}.")


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
    certification = data.get("certification")
    if certification is not None:
        title.certification = deserialize(certification, model.Certification)
    advisories = data.get("advisories")
    if advisories is not None:
        title.advisories = deserialize(advisories, model.Advisories)


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
    certification = data.get("certification")
    if certification is not None:
        title.certification = deserialize(certification, model.Certification)
    advisories = data.get("advisories")
    if advisories is not None:
        title.advisories = deserialize(advisories, model.Advisories)


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
        httpx_kwargs: Extra curl_cffi request kwargs (e.g. proxy, impersonate).
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
        httpx_kwargs: Extra curl_cffi request kwargs (e.g. proxy, impersonate).
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
) -> str:
    """Build search URL with parameters."""
    params: dict[str, Any] = {
        "q": query,
        "s": "tt",
    }
    url_params = urlencode(params)
    return spec.url % {"url_params": url_params}


def _build_suggestion_url(query: str) -> str:
    normalized = "_".join(query.lower().split())
    slug = quote(normalized, safe="_")
    first_char = "x"
    if slug:
        first = slug[0]
        if first.isalnum():
            first_char = first
    return f"{_SUGGESTION_BASE_URL}/{first_char}/{slug}.json"


def _parse_suggestion_year(
    item: dict[str, Any],
) -> tuple[int | None, int | None]:
    start_year = item.get("y")
    if isinstance(start_year, int):
        return start_year, None

    raw_range = item.get("yr")
    if not isinstance(raw_range, str) or not raw_range:
        return None, None

    normalized = raw_range.replace("–", "-")
    start_text, _, end_text = normalized.partition("-")

    start = None
    if start_text.isdigit():
        start = int(start_text)

    end = None
    if end_text.isdigit():
        end = int(end_text)
    return start, end


def _get_suggestion_type_id(item: dict[str, Any]) -> str | None:
    raw_type_id = item.get("qid")
    if isinstance(raw_type_id, str) and raw_type_id:
        return raw_type_id

    raw_type = item.get("q")
    if isinstance(raw_type, str):
        return _SUGGESTION_TYPE_MAP.get(raw_type.lower())
    return None


def _extract_suggestion_results(
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_items = payload.get("d")
    if not isinstance(raw_items, list):
        return []

    results: list[dict[str, Any]] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        imdb_id = item.get("id")
        title = item.get("l")
        if not isinstance(imdb_id, str) or not imdb_id.startswith("tt"):
            continue
        if not isinstance(title, str) or not title:
            continue

        type_id = _get_suggestion_type_id(item)
        if type_id is None:
            continue

        result: dict[str, Any] = {
            "imdb_id": imdb_id,
            "type_id": type_id,
            "title": title,
        }

        start_year, end_year = _parse_suggestion_year(item)
        if start_year is not None:
            result["year"] = start_year
        if end_year is not None:
            result["end_year"] = end_year

        raw_image = item.get("i")
        if isinstance(raw_image, dict):
            image_url = raw_image.get("imageUrl")
            if isinstance(image_url, str) and image_url:
                result["primary_image"] = image_url

        results.append(result)
    return results


def _search_titles_via_html(
    query: str,
    headers: dict[str, str] | None,
    httpx_kwargs: dict[str, Any] | None,
) -> list[model.Title]:
    spec = _spec("title_search")
    url = _build_search_url(spec, query)
    document = _http_client.fetch(
        url, headers=headers, httpx_kwargs=httpx_kwargs
    )
    data = spec.scrape(document, doctype=spec.doctype)
    return _parse_search_results(data.get("results", []))


async def _search_titles_via_html_async(
    query: str,
    headers: dict[str, str] | None,
    httpx_kwargs: dict[str, Any] | None,
) -> list[model.Title]:
    spec = _spec("title_search")
    url = _build_search_url(spec, query)
    document = await _http_client.fetch_async(
        url, headers=headers, httpx_kwargs=httpx_kwargs
    )
    data = spec.scrape(document, doctype=spec.doctype)
    return _parse_search_results(data.get("results", []))


def _parse_year_bound(value: str | int | float | None) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if not isinstance(value, str):
        return None

    year_text = value.strip().split("-", 1)[0]
    if not year_text:
        return None
    try:
        return int(year_text)
    except ValueError:
        return None


def _title_matches_filters(
    title: model.Title,
    filters: model.SearchFilters,
) -> bool:
    if filters.title_types and title.type_id not in filters.title_types:
        return False

    if filters.genres:
        if not title.genres:
            return True
        title_genres = {genre.lower() for genre in title.genres}
        required_genres = {genre.lower() for genre in filters.genres}
        if not required_genres.issubset(title_genres):
            return False

    if filters.release_date:
        if title.year is None:
            return True
        min_year = _parse_year_bound(filters.release_date.min_value)
        max_year = _parse_year_bound(filters.release_date.max_value)
        if min_year is not None and title.year < min_year:
            return False
        if max_year is not None and title.year > max_year:
            return False

    if filters.user_rating:
        if title.rating is None:
            return True
        rating = float(title.rating)
        if (
            filters.user_rating.min_value is not None
            and rating < filters.user_rating.min_value
        ):
            return False
        if (
            filters.user_rating.max_value is not None
            and rating > filters.user_rating.max_value
        ):
            return False

    if filters.votes:
        vote_count = title.vote_count
        if (
            filters.votes.min_value is not None
            and vote_count < filters.votes.min_value
        ):
            return False
        if (
            filters.votes.max_value is not None
            and vote_count > filters.votes.max_value
        ):
            return False

    if filters.runtime:
        if title.runtime is None:
            return True
        if (
            filters.runtime.min_value is not None
            and title.runtime < filters.runtime.min_value
        ):
            return False
        if (
            filters.runtime.max_value is not None
            and title.runtime > filters.runtime.max_value
        ):
            return False

    return True


def _apply_search_filters(
    titles: list[model.Title],
    filters: model.SearchFilters | None,
) -> list[model.Title]:
    if filters is None:
        return titles
    return [
        title
        for title in titles
        if _title_matches_filters(title, filters)
    ]


def _apply_search_sort(
    titles: list[model.Title],
    sort: model.SortCriteria,
) -> list[model.Title]:
    if sort.field in (model.SortField.POPULARITY, model.SortField.BOX_OFFICE):
        return titles

    reverse = sort.order is model.SortOrder.DESCENDING
    if sort.field is model.SortField.ALPHABETICAL:
        return sorted(
            titles,
            key=lambda title: title.sort_title.lower(),
            reverse=reverse,
        )
    if sort.field is model.SortField.USER_RATING:
        return sorted(
            titles,
            key=lambda title: (
                float(title.rating)
                if title.rating is not None else -1.0
            ),
            reverse=reverse,
        )
    if sort.field is model.SortField.NUM_VOTES:
        return sorted(
            titles,
            key=lambda title: title.vote_count,
            reverse=reverse,
        )
    if sort.field is model.SortField.RUNTIME:
        return sorted(
            titles,
            key=lambda title: (
                title.runtime
                if title.runtime is not None else -1
            ),
            reverse=reverse,
        )
    if sort.field is model.SortField.YEAR:
        return sorted(
            titles,
            key=lambda title: title.year if title.year is not None else -1,
            reverse=reverse,
        )
    return titles


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
        httpx_kwargs: Extra curl_cffi request kwargs (e.g. proxy, impersonate).

    Returns:
        List of Title objects
    """
    count = min(count, 100)
    suggestion_url = _build_suggestion_url(query)
    try:
        suggestion_document = _http_client.fetch(
            suggestion_url, headers=headers, httpx_kwargs=httpx_kwargs
        )
        suggestion_data = json.loads(suggestion_document)
        titles = _parse_search_results(
            _extract_suggestion_results(suggestion_data)
        )
    except (curl_requests.exceptions.RequestException, ValueError):
        titles = _search_titles_via_html(query, headers, httpx_kwargs)
    titles = _apply_search_filters(titles, filters)
    titles = _apply_search_sort(titles, sort)

    if not titles and filters is not None:
        try:
            titles = _search_titles_via_html(query, headers, httpx_kwargs)
            titles = _apply_search_filters(titles, filters)
            titles = _apply_search_sort(titles, sort)
        except (
            curl_requests.exceptions.RequestException,
            RuntimeError,
            TypeError,
            ValueError,
        ):
            pass

    if not paginate:
        return titles[:count]

    # The /find endpoint currently exposes a single result page.
    if total_count is None:
        return titles
    return titles[:total_count]


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
        httpx_kwargs: Extra curl_cffi request kwargs (e.g. proxy, impersonate).

    Returns:
        List of Title objects
    """
    count = min(count, 100)
    suggestion_url = _build_suggestion_url(query)
    try:
        suggestion_document = await _http_client.fetch_async(
            suggestion_url, headers=headers, httpx_kwargs=httpx_kwargs
        )
        suggestion_data = json.loads(suggestion_document)
        titles = _parse_search_results(
            _extract_suggestion_results(suggestion_data)
        )
    except (curl_requests.exceptions.RequestException, ValueError):
        titles = await _search_titles_via_html_async(
            query, headers, httpx_kwargs
        )
    titles = _apply_search_filters(titles, filters)
    titles = _apply_search_sort(titles, sort)

    if not titles and filters is not None:
        try:
            titles = await _search_titles_via_html_async(
                query, headers, httpx_kwargs
            )
            titles = _apply_search_filters(titles, filters)
            titles = _apply_search_sort(titles, sort)
        except (
            curl_requests.exceptions.RequestException,
            RuntimeError,
            TypeError,
            ValueError,
        ):
            pass

    if not paginate:
        return titles[:count]

    # The /find endpoint currently exposes a single result page.
    if total_count is None:
        return titles
    return titles[:total_count]
