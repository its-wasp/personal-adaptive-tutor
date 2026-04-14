import httpx

from app.config import settings
from app.search.base_provider import BaseSearchProvider


class SearxngProvider(BaseSearchProvider):

    def __init__(self):
        self.base_url = settings.SEARXNG_URL

    def search(self, query: str, categories: str = "general", num_results: int = 5) -> list[dict]:
        """
        Query the local SearXNG instance and return structured results.

        Args:
            query: Search query string
            categories: SearXNG categories (general, videos, images, news, etc.)
            num_results: Maximum number of results to return
        """
        response = httpx.get(
            f"{self.base_url}/search",
            params={
                "q": query,
                "format": "json",
                "categories": categories,
            },
            timeout=10.0
        )
        response.raise_for_status()

        results = response.json().get("results", [])

        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            }
            for r in results[:num_results]
        ]
