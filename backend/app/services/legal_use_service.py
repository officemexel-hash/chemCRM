import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import new_uuid
from app.db.models.substance import Substance
from app.db.models.tariff import LegalUseDescription

logger = logging.getLogger(__name__)


class LegalUseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def suggest_legal_uses(self, substance_id: str, destination_country: str | None = None) -> list[LegalUseDescription]:
        """Suggest lawful use descriptions for customs declarations."""
        statement = select(LegalUseDescription).where(LegalUseDescription.substance_id == substance_id)
        if destination_country:
            statement = statement.where(
                (LegalUseDescription.destination_country == destination_country.upper())
                | (LegalUseDescription.destination_country.is_(None))
            )
        return list(self.db.scalars(statement))

    def generate_customs_declaration_text(self, substance_id: str, hs_code: str, destination_country: str) -> str:
        """Generate a customs declaration description text for a substance."""
        substance = self.db.get(Substance, substance_id)
        if substance is None:
            return ""

        # Build from known data
        parts: list[str] = []
        if substance.primary_name:
            parts.append(substance.primary_name)
        if substance.cas:
            parts.append(f"CAS: {substance.cas}")
        if hs_code:
            parts.append(f"HS: {hs_code}")

        # Add legal use descriptions
        uses = self.suggest_legal_uses(substance_id, destination_country)
        if uses:
            best_use = uses[0]
            parts.append(f"Use: {best_use.description}")

        # Build declaration text
        declaration = " | ".join(parts)
        return declaration

    def add_legal_use(
        self,
        substance_id: str,
        description: str,
        category: str | None = None,
        destination_country: str | None = None,
        hs_code_id: str | None = None,
        source: str | None = None,
    ) -> LegalUseDescription:
        """Add a new legal use description for a substance."""
        entry = LegalUseDescription(
            id=new_uuid(),
            substance_id=substance_id,
            hs_code_id=hs_code_id,
            description=description,
            category=category,
            destination_country=destination_country.upper() if destination_country else None,
            source=source,
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry
