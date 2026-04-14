from abc import ABC, abstractmethod


class BaseSearchProvider(ABC):

    @abstractmethod
    def search(self, query: str, categories: str = "general", num_results: int = 5) -> list[dict]:
        """
        Search for content and return a list of results.

        Each result is a dict with keys: title, url, snippet
        """
        pass
