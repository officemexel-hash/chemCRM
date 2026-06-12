from app.search_providers.base import SearchResult


class MockSearchProvider:
    provider_name = "mock"

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        return [
            SearchResult(
                title=f"Demo chemical supplier result {rank}",
                url=f"https://example-supplier-{rank}.test/products?query={query.replace(' ', '+')}",
                snippet="Mock legal B2B search result for tests and demos.",
                provider=self.provider_name,
                query=query,
                rank=rank,
            )
            for rank in range(1, min(limit, 5) + 1)
        ]
