from pydantic import BaseModel


class ReportGenerateRequest(BaseModel):
    campaign_id: str
    format: str = "pdf"  # pdf or xlsx
    include_charts: bool = True
    include_ranking: bool = True


class RankingRow(BaseModel):
    rank: int
    quote_id: str
    supplier_name: str
    country: str | None = None
    total_score: float
    price_score: float
    supplier_quality_score: float
    risk_score: float
    document_completeness: float
    recommended: bool
    price: str | None = None
    currency: str | None = None
    lead_time: str | None = None
    incoterms: str | None = None
