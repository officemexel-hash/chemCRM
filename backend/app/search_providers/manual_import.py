from app.search_providers.base import SearchResult
from app.utils.urls import normalize_url


class ManualImportProvider:
    provider_name = "manual_import"

    def __init__(self, urls: list[str] | None = None) -> None:
        self.urls = urls or []

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        return [
            SearchResult(
                title=f"Manual URL import {index}",
                url=normalize_url(url),
                snippet="Manually imported URL; user is responsible for verifying lawful use and terms.",
                provider=self.provider_name,
                query=query,
                rank=index,
            )
            for index, url in enumerate(self.urls[:limit], 1)
        ]
