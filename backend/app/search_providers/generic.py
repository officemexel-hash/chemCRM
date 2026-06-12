from app.search_providers.base import SearchResult


class GenericSearchProvider:
    """Adapter placeholder for a lawful Search API such as SerpAPI/Bing API/custom index."""

    provider_name = "generic"

    def __init__(self, api_key: str | None = None, endpoint: str | None = None) -> None:
        self.api_key = api_key
        self.endpoint = endpoint

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not self.api_key or not self.endpoint:
            return []
        raise NotImplementedError("Configure a lawful Search API implementation before use.")
