from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.quote import Quote
from app.db.session import get_db
from app.schemas.quote import QuotePatch, QuoteRead
from app.services.audit_log import AuditLogService


router = APIRouter(prefix="/quotes", tags=["quotes"])


@router.get("", response_model=list[QuoteRead])
def list_quotes(db: Session = Depends(get_db)) -> list[Quote]:
    return list(db.scalars(select(Quote).order_by(Quote.created_at.desc())))


@router.get("/{quote_id}", response_model=QuoteRead)
def get_quote(quote_id: str, db: Session = Depends(get_db)) -> Quote:
    quote = db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    return quote


@router.patch("/{quote_id}", response_model=QuoteRead)
def patch_quote(quote_id: str, payload: QuotePatch, db: Session = Depends(get_db)) -> Quote:
    quote = db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(quote, field, value)
    AuditLogService(db).log("quote_updated", "quote", quote.id, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(quote)
    return quote


@router.post("/{quote_id}/mark-reviewed", response_model=QuoteRead)
def mark_reviewed(quote_id: str, db: Session = Depends(get_db)) -> Quote:
    quote = db.get(Quote, quote_id)
    if quote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quote not found")
    quote.status = "reviewed"
    AuditLogService(db).log("quote_marked_reviewed", "quote", quote.id)
    db.commit()
    db.refresh(quote)
    return quote
