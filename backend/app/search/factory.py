from app.search.base_provider import BaseSearchProvider
from app.search.searxng_provider import SearxngProvider


def get_search_provider() -> BaseSearchProvider:
    """
    Factory to get the active search provider.

    Currently only SearXNG is supported.
    Extend this with other providers (e.g., Google, Brave) as needed.
    """
    return SearxngProvider()
