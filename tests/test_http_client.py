import asyncio

from cinemagoerng.web import HTTPClient, set_default_http_client


def test_http_client_fetch_impl_bypasses_curl() -> None:
    calls: list[tuple[str, dict[str, str], dict | None]] = []

    def fetch_impl(
        url: str,
        headers: dict[str, str],
        httpx_kwargs: dict | None,
    ) -> str:
        calls.append((url, headers, httpx_kwargs))
        return "<html></html>"

    client = HTTPClient(fetch_impl=fetch_impl)
    out = client.fetch("https://example.com/foo")
    assert out == "<html></html>"
    assert len(calls) == 1
    assert calls[0][0] == "https://example.com/foo"


def test_http_client_fetch_async_impl_bypasses_curl() -> None:
    async def fetch_async_impl(
        url: str,
        headers: dict[str, str],
        httpx_kwargs: dict | None,
    ) -> str:
        return f"body:{url}"

    client = HTTPClient(fetch_async_impl=fetch_async_impl)
    out = asyncio.run(client.fetch_async("https://example.com/bar"))
    assert out == "body:https://example.com/bar"


def test_http_client_fetch_async_uses_sync_impl_via_thread() -> None:
    calls: list[str] = []

    def fetch_impl(
        url: str,
        headers: dict[str, str],
        httpx_kwargs: dict | None,
    ) -> str:
        calls.append(url)
        return "sync"

    client = HTTPClient(fetch_impl=fetch_impl)
    out = asyncio.run(client.fetch_async("https://example.com/baz"))
    assert out == "sync"
    assert calls == ["https://example.com/baz"]


def test_set_default_http_client_updates_module_client() -> None:
    import cinemagoerng.web as web

    prev = web._http_client
    try:
        custom = HTTPClient(
            fetch_impl=lambda url, h, kw: "<html></html>",
        )
        set_default_http_client(custom)
        assert web._http_client is custom
    finally:
        set_default_http_client(prev)
