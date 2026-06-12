from dataclasses import dataclass, field

from bs4 import BeautifulSoup

from app.extractors.contact_extractor import ContactExtractor, ExtractedContact


@dataclass(frozen=True)
class ExtractedSupplier:
    name: str | None
    website: str
    country: str | None = None
    contacts: list[ExtractedContact] = field(default_factory=list)
    products: list[dict] = field(default_factory=list)


class SupplierExtractor:
    def extract(self, html: str, source_url: str) -> ExtractedSupplier:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else None
        extractor = ContactExtractor()
        return ExtractedSupplier(
            name=title,
            website=source_url,
            contacts=extractor.extract(html, source_url),
            products=extractor.extract_products(html),
        )
