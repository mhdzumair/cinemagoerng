# CinemagoerNG

CinemagoerNG is a Python library and command-line utility
for retrieving data from IMDb.
It provides a clean, modern API for accessing movie, TV show,
and celebrity information from IMDb.

> [!Note]
> This project and its authors are not affiliated
> with the Internet Movie Database Inc.
> See the [`DISCLAIMER.txt`](DISCLAIMER.txt)
> file for details about terms of use.

## Features

- Retrieve comprehensive movie and TV show information.
- Support for alternate titles (AKAs).
- Taglines and parental guide information.
- Episode data for TV series.
- Modern Python typing support.
- Clean, intuitive API.

## Installation

CinemagoerNG supports Python 3.11 and later versions.
You can install it using pip:

```bash
pip install cinemagoerng
```

## Basic usage

Here's a simple example of retrieving movie information:

```python
from cinemagoerng import web as imdb

# Get basic movie information
movie = imdb.get_title("tt0133093")  # The Matrix
print(movie.title)       # "The Matrix"
print(movie.sort_title)  # "Matrix"
print(movie.year)        # 1999
print(movie.runtime)     # 136

# Access movie genres
for genre in movie.genres:
    print(genre)         # "Action", "Sci-Fi"

# Get director information
for credit in movie.directors:
    print(credit.name)   # "Lana Wachowski", "Lilly Wachowski"
```

### Retrieving additional information

You can fetch additional details using the relevant `set_` functions:

```python
# Set all taglines
imdb.set_taglines(movie)
for tagline in movie.taglines:
    print(tagline)

# Get alternate titles (AKAs)
imdb.set_akas(movie)
for aka in movie.akas:
    print(f"{aka.title} ({aka.country})")
```

## Available data

CinemagoerNG can retrieve various types of information:

### Basic information

- Title
- Year
- Runtime
- Genres
- Plot summary
- Rating
- Number of votes

### Credits

- Directors
- Writers
- Cast members
- Producers
- Composers
- Crew members

### Additional details

- Taglines
- Alternative titles (AKAs)
- Episode information (for TV series)
- Parental guide

## HTTP client, blocking, and proxies

CinemagoerNG loads public IMDb pages and API-style endpoints using
[curl_cffi](https://github.com/lwthiker/curl-impersonate), which can mimic
browser TLS fingerprints and retries with several Chrome/Safari profiles when a
response looks like an empty body or an AWS WAF challenge.

From many datacenter or VPN IPs, IMDb may still return empty bodies or
challenge pages. In that case you can:

- Pass extra **`headers`** (for example a `Cookie` header from a real browser
  session) or **`httpx_kwargs`** to **`get_title`**, **`get_title_async`**,
  **`search_titles`**, and the various **`set_*`** helpers. Those keyword
  arguments are forwarded into curl_cffi (see its docs for **`proxy`** /
  **`proxies`**, timeouts, and **`impersonate`**).
- Install a custom client with **`fetch_impl`** / **`fetch_async_impl`** (below)
  so pages are loaded with a real browser or another stack you control.

## Pluggable fetch (browser automation)

The default module client is a **`cinemagoerng.web.HTTPClient`**. You can
replace it globally with **`cinemagoerng.web.set_default_http_client`**, or keep
separate instances if you build your own wiring.

Custom hooks receive **`(url, merged_headers, httpx_kwargs)`** and must return
the response body as a **`str`**. The library merges browser-like headers for
`www.imdb.com` HTML requests, then validates title/reference pages the same way
as the built-in path (empty or WAF-style HTML still raises a clear error).

Sync-only hook (async **`get_title_async`** will run the sync hook in a
thread pool):

```python
from cinemagoerng.web import HTTPClient, set_default_http_client

def fetch_impl(url, headers, httpx_kwargs):
    # Example: use Playwright, requests with rotating proxies, etc.
    # return page_html_string
    ...

set_default_http_client(HTTPClient(fetch_impl=fetch_impl))
```

Optional dedicated async hook:

```python
async def fetch_async_impl(url, headers, httpx_kwargs):
    ...

client = HTTPClient(fetch_async_impl=fetch_async_impl)
set_default_http_client(client)
```

## Development

It is recommended to use `uv` for development:

```bash
# Clone the repository
git clone https://codeberg.org/cinemagoer/cinemagoerng.git
cd cinemagoerng

# Set up environment
uv sync

# Run tests
uv run pytest

# Run type checks
uv run mypy src tests

# Check code style
uv run ruff check --preview src tests

# Test under all supported Python versions
uv run tox
```

## License

This project is licensed under the
GNU Lesser General Public License v3 or later - see the
[`LICENSE.txt`](LICENSE.txt) file for details.

## Acknowledgments

CinemagoerNG is a modern reimagining of the original
[Cinemagoer/IMDbPY](https://github.com/cinemagoer/cinemagoer) project.
Special thanks to:

- All contributors to the original Cinemagoer (IMDbPY) project.
- The IMDb website for providing the data.
