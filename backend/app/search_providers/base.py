from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    provider: str
    query: str
    rank: int


class SearchProvider(Protocol):
    provider_name: str

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        ...
