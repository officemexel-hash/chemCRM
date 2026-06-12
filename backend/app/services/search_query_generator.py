from dataclasses import dataclass


@dataclass(frozen=True)
class SearchQuery:
    query: str
    priority: int
    source_reason: str


def generate_search_queries(
    cas: str, primary_name: str | None = None, synonyms: list[str] | None = None
) -> list[SearchQuery]:
    templates: list[tuple[str, int, str]] = [
        (f"{cas} supplier", 100, "CAS supplier search"),
        (f"{cas} manufacturer", 95, "CAS manufacturer search"),
        (f"{cas} bulk", 90, "CAS bulk availability"),
        (f"{cas} COA", 80, "CAS COA evidence"),
        (f"{cas} SDS", 80, "CAS SDS evidence"),
    ]
    if primary_name:
        templates.extend(
            [
                (f"{primary_name} supplier", 85, "primary name supplier search"),
                (f"{primary_name} manufacturer", 82, "primary name manufacturer search"),
                (f"{primary_name} technical grade", 76, "grade-specific search"),
                (f"{primary_name} REACH supplier Europe", 72, "EU compliance search"),
            ]
        )
    for synonym in synonyms or []:
        if synonym and synonym != primary_name:
            templates.append((f"{synonym} supplier", 60, "synonym supplier search"))
            templates.append((f"{synonym} manufacturer", 58, "synonym manufacturer search"))

    seen: set[str] = set()
    queries: list[SearchQuery] = []
    for query, priority, reason in templates:
        normalized = " ".join(query.split())
        key = normalized.lower()
        if key not in seen:
            queries.append(SearchQuery(normalized, priority, reason))
            seen.add(key)
    return queries
