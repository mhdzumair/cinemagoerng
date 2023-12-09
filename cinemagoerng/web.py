# Copyright 2023 H. Turgut Uyar <uyar@tekir.org>
#
# CinemagoerNG is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# CinemagoerNG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CinemagoerNG; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import json
from functools import lru_cache
from http import HTTPStatus
from pathlib import Path
from typing import Literal, TypeAlias, TypeVar
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from .model import Title
from .piculet import Spec, deserialize, load_spec, scrape, serialize


_USER_AGENT = " ".join([
    "Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B)",
    "AppleWebKit/535.19 (KHTML, like Gecko)",
    "Chrome/18.0.1025.133 Mobile Safari/535.19",
])


def fetch(url: str, /) -> str:
    request = Request(url)
    request.add_header("User-Agent", _USER_AGENT)
    with urlopen(request) as response:
        content: bytes = response.read()
    return content.decode("utf-8")


SPECS_DIR = Path(__file__).parent / "specs"

Title_ = TypeVar("Title_", bound=Title)
TitlePage: TypeAlias = Literal["main", "reference", "taglines"]


@lru_cache(maxsize=None)
def _spec(page: str, /) -> Spec:
    path = SPECS_DIR / f"{page}.json"
    content = path.read_text(encoding="utf-8")
    return load_spec(json.loads(content))


def get_title(imdb_id: str, *, page: TitlePage = "main") -> Title | None:
    spec = _spec(f"title_{page}")
    url = spec.url % {"imdb_id": imdb_id}
    try:
        document = fetch(url)
    except HTTPError as e:
        if e.status == HTTPStatus.NOT_FOUND:
            return None
        raise e  # pragma: no cover
    data = scrape(document, spec.rules)
    return deserialize(data, Title)  # type: ignore


def update_title(title: Title_, /, *, page: TitlePage) -> Title_:
    spec = _spec(f"title_{page}")
    url = spec.url % {"imdb_id": title.imdb_id}
    document = fetch(url)
    data = scrape(document, spec.rules)
    current_data = serialize(title)
    return deserialize(current_data | data, title.__class__)
