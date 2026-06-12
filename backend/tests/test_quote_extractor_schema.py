from app.services.quote_extractor import ExtractedQuote, QuoteExtractor


def test_quote_extractor_returns_valid_schema() -> None:
    result = QuoteExtractor().extract(
        "CAS 64-17-5 confirmed. Price: USD 12.50/kg EXW. MOQ: 25 kg. "
        "Lead time: 14 days. COA and SDS available. Payment: TT. REACH: available."
    )
    validated = ExtractedQuote.model_validate(result.model_dump())
    assert validated.prices
    assert validated.prices[0].price == 12.5
    assert validated.coa_available is True
    assert validated.sds_available is True
