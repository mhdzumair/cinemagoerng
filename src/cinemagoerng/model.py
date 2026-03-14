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

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum, auto
from typing import Any, Generic, Literal, TypeAlias, TypeVar
from urllib.parse import urlparse

from . import linguistics, lookup


T = TypeVar("T", int, float, str)


@dataclass(kw_only=True)
class Person:
    imdb_id: str
    name: str


@dataclass
class _Credit:
    person: Person
    notes: list[str] = field(default_factory=list)

    @property
    def imdb_id(self) -> str:
        return self.person.imdb_id

    @property
    def name(self) -> str:
        return self.person.name

    @property
    def as_name(self) -> str | None:
        as_notes = [note for note in self.notes if note.startswith("as ")]
        return as_notes[0][3:] if len(as_notes) > 0 else None

    @property
    def uncredited(self) -> bool:
        return "uncredited" in self.notes


@dataclass(kw_only=True)
class CrewCredit(_Credit):
    job: str | None = None


@dataclass(kw_only=True)
class CastCredit(_Credit):
    characters: list[str] = field(default_factory=list)


@dataclass
class AKA:
    title: str
    country_code: str | None = None
    language_code: str | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def country(self) -> str | None:
        if self.country_code is None:
            return None
        return lookup.COUNTRY_CODES.get(self.country_code, None)

    @property
    def language(self) -> str | None:
        if self.language_code is None:
            return None
        return lookup.LANGUAGE_CODES.get(self.language_code.upper(), None)


@dataclass(kw_only=True)
class Certificate:
    country: str
    ratings: list[str]


@dataclass(kw_only=True)
class Certification:
    mpa_rating: str | None = "Not Rated"
    mpa_rating_reason: str | None = None
    certificates: list[Certificate] = field(default_factory=list)


@dataclass(kw_only=True)
class AdvisoryVotes:
    none: int = 0
    mild: int = 0
    moderate: int = 0
    severe: int = 0


@dataclass(kw_only=True)
class AdvisoryDetail:
    text: str
    is_spoiler: bool


AdvisoryStatus: TypeAlias = Literal[
    "Unknown", "None", "Mild", "Moderate", "Severe"
]


@dataclass(kw_only=True)
class Advisory:
    details: list[AdvisoryDetail] = field(default_factory=list)
    status: AdvisoryStatus = "Unknown"
    votes: AdvisoryVotes = field(default_factory=AdvisoryVotes)


@dataclass(kw_only=True)
class Advisories:
    nudity: Advisory = field(default_factory=Advisory)
    violence: Advisory = field(default_factory=Advisory)
    profanity: Advisory = field(default_factory=Advisory)
    alcohol: Advisory = field(default_factory=Advisory)
    frightening: Advisory = field(default_factory=Advisory)


@dataclass(kw_only=True)
class _Title:
    imdb_id: str
    title: str

    primary_image: str | None = None

    year: int | None = None
    release_date: date | None = None
    country_codes: list[str] = field(default_factory=list)
    language_codes: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    taglines: list[str] = field(default_factory=list)
    plot: dict[str, str] = field(default_factory=dict)
    plot_summaries: dict[str, list[str]] = field(default_factory=dict)

    rating: Decimal | None = None
    vote_count: int = 0
    top_ranking: int | None = None

    cast: list[CastCredit] = field(default_factory=list)
    directors: list[CrewCredit] = field(default_factory=list)
    writers: list[CrewCredit] = field(default_factory=list)
    producers: list[CrewCredit] = field(default_factory=list)
    composers: list[CrewCredit] = field(default_factory=list)
    cinematographers: list[CrewCredit] = field(default_factory=list)
    editors: list[CrewCredit] = field(default_factory=list)
    casting_directors: list[CrewCredit] = field(default_factory=list)
    production_designers: list[CrewCredit] = field(default_factory=list)
    art_directors: list[CrewCredit] = field(default_factory=list)
    set_decorators: list[CrewCredit] = field(default_factory=list)
    costume_designers: list[CrewCredit] = field(default_factory=list)
    makeup_department: list[CrewCredit] = field(default_factory=list)
    production_management: list[CrewCredit] = field(default_factory=list)
    assistant_directors: list[CrewCredit] = field(default_factory=list)
    art_department: list[CrewCredit] = field(default_factory=list)
    sound_department: list[CrewCredit] = field(default_factory=list)
    special_effects: list[CrewCredit] = field(default_factory=list)
    visual_effects: list[CrewCredit] = field(default_factory=list)
    stunts: list[CrewCredit] = field(default_factory=list)
    choreographers: list[CrewCredit] = field(default_factory=list)
    animation_department: list[CrewCredit] = field(default_factory=list)
    camera_department: list[CrewCredit] = field(default_factory=list)
    casting_department: list[CrewCredit] = field(default_factory=list)
    costume_department: list[CrewCredit] = field(default_factory=list)
    editorial_department: list[CrewCredit] = field(default_factory=list)
    location_management: list[CrewCredit] = field(default_factory=list)
    music_department: list[CrewCredit] = field(default_factory=list)
    production_department: list[CrewCredit] = field(default_factory=list)
    script_department: list[CrewCredit] = field(default_factory=list)
    transportation_department: list[CrewCredit] = field(default_factory=list)
    additional_crew: list[CrewCredit] = field(default_factory=list)
    thanks: list[CrewCredit] = field(default_factory=list)

    akas: list[AKA] = field(default_factory=list)

    certification: Certification | None = None
    advisories: Advisories | None = None

    @property
    def countries(self) -> list[str]:
        return [
            lookup.COUNTRY_CODES.get(c.upper(), c.upper())
            for c in self.country_codes
        ]

    @property
    def languages(self) -> list[str]:
        return [
            language
            for c in self.language_codes
            if (language := lookup.LANGUAGE_CODES.get(c.upper())) is not None
        ]

    @property
    def sort_title(self) -> str:
        if len(self.language_codes) > 0:
            primary_lang: str = self.language_codes[0].upper()
            articles = linguistics.ARTICLES.get(primary_lang)
            if articles is not None:
                first, *rest = self.title.split(" ")
                if (len(rest) > 0) and (first.lower() in articles):
                    title = " ".join(rest)
                    if self.title[0].isupper() and title[0].islower():
                        title = title[0].upper() + title[1:]
                    return title
        return self.title


@dataclass(kw_only=True)
class _TimedTitle(_Title):
    runtime: int | None = None


@dataclass(kw_only=True)
class Movie(_TimedTitle):
    type_id: Literal["movie"] = "movie"


@dataclass(kw_only=True)
class TVMovie(_TimedTitle):
    type_id: Literal["tvMovie"] = "tvMovie"


@dataclass(kw_only=True)
class ShortMovie(_TimedTitle):
    type_id: Literal["short"] = "short"


@dataclass(kw_only=True)
class TVShortMovie(_TimedTitle):
    type_id: Literal["tvShort"] = "tvShort"


@dataclass(kw_only=True)
class VideoMovie(_TimedTitle):
    type_id: Literal["video"] = "video"


@dataclass(kw_only=True)
class MusicVideo(_TimedTitle):
    type_id: Literal["musicVideo"] = "musicVideo"


@dataclass(kw_only=True)
class VideoGame(_Title):
    type_id: Literal["videoGame"] = "videoGame"


@dataclass(kw_only=True)
class TVEpisode(_TimedTitle):
    type_id: Literal["tvEpisode"] = "tvEpisode"
    series: TVSeries | TVMiniSeries | None = None
    season: str | None = None
    episode: str | None = None
    release_date: date | None = None
    previous_episode_id: str | None = None
    next_episode_id: str | None = None


@dataclass(kw_only=True)
class _TVSeries(_TimedTitle):
    end_year: int | None = None
    seasons: list[str] = field(default_factory=list)
    episodes: dict[str, dict[str, TVEpisode]] = field(default_factory=dict)
    creators: list[CrewCredit] = field(default_factory=list)


@dataclass(kw_only=True)
class TVSeries(_TVSeries):
    type_id: Literal["tvSeries"] = "tvSeries"


@dataclass(kw_only=True)
class TVMiniSeries(_TVSeries):
    type_id: Literal["tvMiniSeries"] = "tvMiniSeries"


@dataclass(kw_only=True)
class TVSpecial(_TimedTitle):
    type_id: Literal["tvSpecial"] = "tvSpecial"


@dataclass
class PodcastEpisode(_TimedTitle):
    type_id: Literal["podcastEpisode"] = "podcastEpisode"


@dataclass
class PodcastSeries(_TimedTitle):
    type_id: Literal["podcastSeries"] = "podcastSeries"


Title: TypeAlias = (
    Movie
    | TVMovie
    | ShortMovie
    | TVShortMovie
    | VideoMovie
    | MusicVideo
    | VideoGame
    | TVSeries
    | TVMiniSeries
    | TVEpisode
    | TVSpecial
    | PodcastEpisode
    | PodcastSeries
)


class SortField(Enum):
    """Available fields for sorting search results."""

    POPULARITY = auto()
    ALPHABETICAL = auto()
    USER_RATING = auto()
    NUM_VOTES = auto()
    BOX_OFFICE = auto()
    RUNTIME = auto()
    YEAR = auto()


class SortOrder(Enum):
    """Sort order for search results."""

    ASCENDING = "ASC"
    DESCENDING = "DESC"


@dataclass
class SortCriteria:
    """Criteria for sorting search results."""

    field: SortField
    order: SortOrder = SortOrder.ASCENDING

    def to_url_param(self) -> str:
        """Convert to IMDb URL parameter format."""
        field_map = {
            SortField.POPULARITY: "moviemeter",
            SortField.ALPHABETICAL: "alpha",
            SortField.USER_RATING: "user_rating",
            SortField.NUM_VOTES: "num_votes",
            SortField.BOX_OFFICE: "boxoffice_gross_us",
            SortField.RUNTIME: "runtime",
            SortField.YEAR: "year",
        }
        return f"{field_map[self.field]},{self.order.value.lower()}"

    def to_graphql_params(self) -> tuple[str, str]:
        """Convert to GraphQL parameter format."""
        field_map = {
            SortField.POPULARITY: "POPULARITY",
            SortField.ALPHABETICAL: "ALPHA",
            SortField.USER_RATING: "USER_RATING",
            SortField.NUM_VOTES: "NUM_VOTES",
            SortField.BOX_OFFICE: "BOX_OFFICE",
            SortField.RUNTIME: "RUNTIME",
            SortField.YEAR: "YEAR",
        }
        return field_map[self.field], self.order.value

    @staticmethod
    def from_url(url: str) -> SortCriteria:
        """Parse IMDb URL parameter string to SortCriteria."""
        field_map = {
            "moviemeter": SortField.POPULARITY,
            "alpha": SortField.ALPHABETICAL,
            "user_rating": SortField.USER_RATING,
            "num_votes": SortField.NUM_VOTES,
            "boxoffice_gross_us": SortField.BOX_OFFICE,
            "runtime": SortField.RUNTIME,
            "year": SortField.YEAR,
        }
        # find if the url contain sort criteria
        # then parse it otherwise returns default sorting
        if "sort" in url:
            parsed_url = urlparse(url)
            params = parsed_url.query.split("&")
            for param in params:
                if "sort=" in param:
                    field, order = param.split("=")[1].split(",")
                    return SortCriteria(
                        field_map[field], SortOrder(order.upper())
                    )
        return SortCriteria(SortField.POPULARITY)


@dataclass
class RangeFilter(Generic[T]):
    """Generic range filter for numeric or str values."""

    min_value: T | None = None
    max_value: T | None = None

    def to_param_string(self) -> str:
        """Convert range to IMDb parameter string format."""
        if self.min_value is None and self.max_value is None:
            return ""
        return f"{self.min_value or ''},{self.max_value or ''}"


@dataclass
class SearchFilters:
    """Container for all search filter criteria."""

    title_types: list[str] | None = None
    genres: list[str] | None = None
    countries: list[str] | None = None
    languages: list[str] | None = None
    release_date: RangeFilter[str] | None = None
    user_rating: RangeFilter[float] | None = None
    votes: RangeFilter[int] | None = None
    runtime: RangeFilter[int] | None = None
    adult: bool = True

    def to_url_params(self) -> dict[str, str]:
        """Convert filters to URL parameters."""
        params = {"adult": "include" if self.adult else "exclude"}

        if self.title_types:
            params["title_type"] = ",".join(self.title_types)
        if self.genres:
            params["genres"] = ",".join(self.genres)
        if self.countries:
            params["countries"] = ",".join(self.countries)
        if self.languages:
            params["languages"] = ",".join(self.languages)

        if self.release_date:
            date_param = self.release_date.to_param_string()
            if date_param:
                params["release_date"] = date_param

        if self.user_rating:
            rating_param = self.user_rating.to_param_string()
            if rating_param:
                params["user_rating"] = rating_param

        if self.votes:
            votes_param = self.votes.to_param_string()
            if votes_param:
                params["num_votes"] = votes_param

        if self.runtime:
            runtime_param = self.runtime.to_param_string()
            if runtime_param:
                params["runtime"] = runtime_param

        return params

    def to_graphql_variables(self) -> dict[str, Any]:
        """Convert filters to GraphQL variables."""
        variables: dict[str, Any] = {
            "explicitContentConstraint": {
                "explicitContentFilter": "INCLUDE_ADULT"
                if self.adult
                else "EXCLUDE_ADULT"
            }
        }

        if self.title_types:
            variables["titleTypeConstraint"] = {
                "anyTitleTypeIds": self.title_types,
                "excludeTitleTypeIds": [],
            }

        if self.genres:
            variables["genreConstraint"] = {"allGenreIds": self.genres}

        if self.countries:
            variables["originCountryConstraint"] = {
                "allCountries": self.countries
            }

        if self.languages:
            variables["languageConstraint"] = {"allLanguages": self.languages}

        if self.release_date:
            date_range = {}
            if self.release_date.min_value:
                date_range["start"] = self.release_date.min_value
            if self.release_date.max_value:
                date_range["end"] = self.release_date.max_value
            if date_range:
                variables["releaseDateConstraint"] = {
                    "releaseDateRange": date_range
                }

        if self.user_rating:
            rating_range = {}
            if self.user_rating.min_value is not None:
                rating_range["min"] = self.user_rating.min_value
            if self.user_rating.max_value is not None:
                rating_range["max"] = self.user_rating.max_value
            if rating_range:
                variables["userRatingConstraint"] = {
                    "aggregateRatingRange": rating_range
                }

        if self.votes:
            votes_range = {}
            if self.votes.min_value is not None:
                votes_range["min"] = self.votes.min_value
            if self.votes.max_value is not None:
                votes_range["max"] = self.votes.max_value
            if votes_range:
                variables["ratingsCountRange"] = votes_range

        if self.runtime:
            runtime_range = {}
            if self.runtime.min_value is not None:
                runtime_range["min"] = self.runtime.min_value
            if self.runtime.max_value is not None:
                runtime_range["max"] = self.runtime.max_value
            if runtime_range:
                variables["runtimeConstraint"] = {
                    "runtimeRangeMinutes": runtime_range
                }

        return variables

    @staticmethod
    def from_url(url: str) -> SearchFilters:
        """Parse IMDb URL parameters to SearchFilters."""
        parsed_url = urlparse(url)
        params = parsed_url.query.split("&")
        filters = SearchFilters()
        for param in params:
            key, value = param.split("=")
            if key == "adult":
                filters.adult = value == "include"
            elif key == "title_type":
                filters.title_types = value.split(",")
            elif key == "genres":
                filters.genres = value.split(",")
            elif key == "countries":
                filters.countries = value.split(",")
            elif key == "languages":
                filters.languages = value.split(",")
            elif key == "release_date":
                min_date, max_date = value.split(",")
                filters.release_date = RangeFilter(min_date, max_date)
            elif key == "user_rating":
                min_rating, max_rating = value.split(",")
                filters.user_rating = RangeFilter(
                    float(min_rating), float(max_rating)
                )
            elif key == "num_votes":
                min_votes, max_votes = value.split(",")
                filters.votes = RangeFilter(int(min_votes), int(max_votes))
            elif key == "runtime":
                min_runtime, max_runtime = value.split(",")
                filters.runtime = RangeFilter(
                    int(min_runtime), int(max_runtime)
                )
        return filters
