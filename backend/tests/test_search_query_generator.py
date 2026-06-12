from app.services.search_query_generator import generate_search_queries


def test_search_query_generator_dedupes_and_prioritizes() -> None:
    queries = generate_search_queries("64-17-5", "Ethanol", ["Ethanol", "ethyl alcohol"])
    values = [item.query for item in queries]
    assert "64-17-5 supplier" in values
    assert "Ethanol manufacturer" in values
    assert "ethyl alcohol supplier" in values
    assert len(values) == len(set(value.lower() for value in values))
    assert queries[0].priority >= queries[-1].priority
