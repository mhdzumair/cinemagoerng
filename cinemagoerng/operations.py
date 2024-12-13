# Copyright 2024 H. Turgut Uyar <uyar@tekir.org>
#
# This file is part of CinemagoerNG.
#
# CinemagoerNG is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# CinemagoerNG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CinemagoerNG.  If not, see <http://www.gnu.org/licenses/>.


import json
from abc import ABC, abstractmethod
from typing import (
    Awaitable,
    Callable,
    Generic,
    List,
    Optional,
    TypeVar,
    Union,
)
from urllib.parse import urlencode

from typedload.exceptions import TypedloadValueError

from . import model, piculet


T = TypeVar("T")

FetchFunction = Callable[..., Union[str, Awaitable[str]]]


class Operation(ABC, Generic[T]):
    """Base class for operations that can be performed sync or async."""

    def __init__(self, fetch_func: FetchFunction):
        self.fetch = fetch_func

    @abstractmethod
    def _process_data_sync(self, data: dict, **kwargs) -> T:
        """Process the scraped data synchronously."""
        pass

    @abstractmethod
    async def _process_data_async(self, data: dict, **kwargs) -> T:
        """Process the scraped data asynchronously."""
        pass

    def _get_url(self, spec: piculet.Spec, **kwargs) -> str:
        """Generate URL from spec and parameters."""
        url_params = {}
        if spec.url_default_params:
            url_params.update(spec.url_default_params)
        url_params.update(kwargs)

        if spec.url_transform:
            return spec.url_transform.apply(
                {"url": spec.url, "params": url_params}
            )
        return spec.url % url_params

    def _scrape_document(self, document: str, spec: piculet.Spec) -> dict:
        """Scrape document using the provided spec."""
        return piculet.scrape(
            document,
            doctype=spec.doctype,
            rules=spec.rules,
            pre=spec.pre,
            post=spec.post,
        )

    def execute(self, spec: piculet.Spec, **kwargs) -> T:
        """Execute the operation synchronously."""

        url = self._get_url(spec, **kwargs)
        document = self.fetch(url, **kwargs)
        data = self._scrape_document(document, spec)
        return self._process_data_sync(data, spec=spec, **kwargs)

    async def execute_async(self, spec: piculet.Spec, **kwargs) -> T:
        """Execute the operation asynchronously."""

        url = self._get_url(spec, **kwargs)
        document = await self.fetch(url, **kwargs)
        data = self._scrape_document(document, spec)
        return await self._process_data_async(data, spec=spec, **kwargs)


class GetTitle(Operation[Optional[model.Title]]):
    """Operation for retrieving a single title."""

    def _process_data_sync(
        self, data: dict, **kwargs
    ) -> Optional[model.Title]:
        if not data:
            return None
        return piculet.deserialize(data, model.Title)

    async def _process_data_async(
        self, data: dict, **kwargs
    ) -> Optional[model.Title]:
        return self._process_data_sync(data, **kwargs)


class UpdateTitle(Operation[None]):
    """Operation for updating a title with additional information."""

    def __init__(
        self, fetch_func: FetchFunction, title: model.Title, keys: List[str]
    ):
        super().__init__(fetch_func)
        self.title = title
        self.keys = keys

    def _update_fields(self, data: dict) -> None:
        """Update title fields from data."""
        for key in self.keys:
            value = data.get(key)
            if value is None:
                continue

            if key == "episodes":
                if isinstance(value, dict):
                    value = piculet.deserialize(value, model.EpisodeMap)
                    self.title.episodes.update(value)
                else:
                    value = piculet.deserialize(value, list[model.TVEpisode])
                    self.title.add_episodes(value)
            elif key == "akas":
                value = [piculet.deserialize(aka, model.AKA) for aka in value]
                self.title.akas.extend(value)
            elif key == "certification":
                value = piculet.deserialize(value, model.Certification)
                setattr(self.title, key, value)
            elif key == "advisories":
                value = piculet.deserialize(value, model.Advisories)
                setattr(self.title, key, value)
            else:
                setattr(self.title, key, value)

    def _process_data_sync(self, data: dict, **kwargs) -> None:
        """Process the data synchronously and handle pagination if needed."""
        self._update_fields(data)

        if kwargs.get("paginate_result") and data.get("has_next_page", False):
            kwargs["after"] = f'"{data["end_cursor"]}"'
            self.execute(**kwargs)

    async def _process_data_async(self, data: dict, **kwargs) -> None:
        """Process the data asynchronously and handle pagination if needed."""
        self._update_fields(data)

        if kwargs.get("paginate_result") and data.get("has_next_page", False):
            kwargs["after"] = f'"{data["end_cursor"]}"'
            await self.execute_async(**kwargs)


class SearchTitles(Operation[List[model.Title]]):
    """Operation for searching titles."""

    def __init__(
        self,
        fetch_func: FetchFunction,
        paginate: bool = False,
        target_count: Optional[int] = None,
    ):
        super().__init__(fetch_func)
        self.paginate = paginate
        self.target_count = target_count

    def _get_url(self, spec: piculet.Spec, **kwargs) -> str:
        """Generate URL from spec and parameters."""
        # Prepare URL parameters
        params = {
            "title": kwargs["query"],
            "count": kwargs["count"],
        }

        if kwargs.get("sort"):
            params["sort"] = kwargs["sort"].to_url_param()
        if kwargs.get("filters"):
            params.update(kwargs["filters"].to_url_params())
        url_params = urlencode(params)
        return spec.url % {"url_params": url_params}

    def _parse_results(self, results: List[dict]) -> List[model.Title]:
        """Parse search results into Title objects."""
        titles = []
        for result in results:
            try:
                title = piculet.deserialize(result, model.Title)
                titles.append(title)
            except TypedloadValueError:
                continue
        return titles

    def _prepare_graphql_variables(self, data: dict, **kwargs) -> dict:
        """Prepare variables for GraphQL pagination query."""
        variables = {
            "after": data.get("end_cursor"),
            "first": kwargs.get("count", 50),
            "locale": "en-US",
            "titleTextConstraint": {"searchTerm": kwargs.get("query", "")},
        }

        filters = kwargs.get("filters")
        if filters:
            variables.update(filters.to_graphql_variables())

        sort = kwargs.get("sort")
        if sort:
            sort_field, sort_order = sort.to_graphql_params()
            variables["sortBy"] = sort_field
            variables["sortOrder"] = sort_order

        return variables

    def _prepare_pagination_request(
        self, graphql_variables: dict
    ) -> tuple[str, str]:
        """Prepare GraphQL pagination request parameters."""
        extensions = {
            "persistedQuery": {
                "sha256Hash": "60a7b8470b01671336ffa535b21a0a6cdaf50267fa2ab55b3e3772578a8c1f00",
                "version": 1,
            }
        }
        extensions_json = json.dumps(extensions, separators=(",", ":"))
        variables_json = json.dumps(graphql_variables, separators=(",", ":"))
        return variables_json, extensions_json

    def _process_data_sync(self, data: dict, **kwargs) -> List[model.Title]:
        """Process the data synchronously."""
        titles = self._parse_results(data.get("results", []))

        if not self.paginate:
            return titles

        has_next_page = len(data.get("results", [])) < data.get(
            "total_results", 0
        )
        if not has_next_page:
            return titles

        # Continue with pagination using GraphQL
        spec = kwargs.get("pagination_spec")
        if not spec:
            return titles

        graphql_variables = self._prepare_graphql_variables(data, **kwargs)
        while has_next_page and (
            self.target_count is None or len(titles) < self.target_count
        ):
            variables_json, extensions_json = self._prepare_pagination_request(
                graphql_variables
            )

            url = spec.url % {
                "variables": variables_json,
                "extensions": extensions_json,
            }

            document = self.fetch(
                url,
                httpx_kwargs=kwargs.get("httpx_kwargs"),
                doc_type=spec.doctype,
                variables=graphql_variables,
            )  # type: ignore
            page_data = self._scrape_document(document, spec)

            new_titles = self._parse_results(page_data.get("results", []))
            titles.extend(new_titles)

            has_next_page = page_data.get("has_next_page", False)
            if has_next_page:
                graphql_variables["after"] = page_data.get("end_cursor")

        return titles

    async def _process_data_async(
        self, data: dict, **kwargs
    ) -> List[model.Title]:
        """Process the data asynchronously."""
        titles = self._parse_results(data.get("results", []))

        if not self.paginate:
            return titles

        has_next_page = len(data.get("results", [])) < data.get(
            "total_results", 0
        )
        if not has_next_page:
            return titles

        # Continue with pagination using GraphQL
        spec = kwargs.get("pagination_spec")
        if not spec:
            return titles

        graphql_variables = self._prepare_graphql_variables(data, **kwargs)
        while has_next_page and (
            self.target_count is None or len(titles) < self.target_count
        ):
            variables_json, extensions_json = self._prepare_pagination_request(
                graphql_variables
            )

            url = spec.url % {
                "variables": variables_json,
                "extensions": extensions_json,
            }

            document = await self.fetch(
                url,
                httpx_kwargs=kwargs.get("httpx_kwargs"),
                doc_type=spec.doctype,
                variables=graphql_variables,
            )  # type: ignore
            page_data = self._scrape_document(document, spec)

            new_titles = self._parse_results(page_data.get("results", []))
            titles.extend(new_titles)

            has_next_page = page_data.get("has_next_page", False)
            if has_next_page:
                graphql_variables["after"] = page_data.get("end_cursor")

        return titles
