from datetime import datetime, timezone
from html import escape
from uuid import uuid4

from app.schemas.documents import (
    CompanyLetterheadData,
    INCOTERMS_RESPONSIBILITY,
    TRANSPORT_INCOTERMS,
    IncotermsGuideResponse,
    LetterOfIntentRequest,
    LetterOfIntentResponse,
    LetterheadRequest,
    LetterheadResponse,
    PurchaseOrderRequest,
    PurchaseOrderResponse,
)


class DocumentGenerator:
    """Generate procurement documents as HTML and plain text."""

    def generate_letterhead(self, request: LetterheadRequest) -> LetterheadResponse:
        company = request.company or CompanyLetterheadData()
        html = _html_shell(
            title=request.title or "Company letterhead",
            company=company,
            reference_number=request.reference_number,
            body_html=f"<h1>{escape(request.title or 'Company Letterhead')}</h1>",
            date=request.date,
        )
        text = _letterhead_text(company, request.reference_number, request.date, request.title)
        return LetterheadResponse(html=html, text=text)

    def generate_loi(self, request: LetterOfIntentRequest) -> LetterOfIntentResponse:
        company = request.company or CompanyLetterheadData()
        ref = request.reference_number or f"LOI-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}"
        subject = f"Letter of Intent - {request.substance_name} / CAS {request.substance_cas}"
        body_html = f"""
<h1>Letter of Intent</h1>
<p>To: <strong>{escape(request.recipient_name)}</strong>, {escape(request.recipient_company)}</p>
<p>Dear {escape(request.recipient_name)},</p>
<p>
  This Letter of Intent confirms that <strong>{escape(company.legal_name or '[Company]')}</strong>
  intends to evaluate procurement of the chemical product listed below, subject to supplier due
  diligence, product documentation, lawful end-use verification, and final commercial agreement.
</p>
<table>
  <tr><th>Product</th><td>{escape(request.substance_name)}</td></tr>
  <tr><th>CAS</th><td>{escape(request.substance_cas)}</td></tr>
  <tr><th>Quantity</th><td>{escape(request.quantity or 'To be confirmed')}</td></tr>
  <tr><th>Destination</th><td>{escape(request.destination_country or 'To be confirmed')}</td></tr>
  <tr><th>Intended lawful use</th><td>{escape(request.intended_use or 'Industrial chemical use by qualified personnel')}</td></tr>
  {f"<tr><th>Notes</th><td>{escape(request.additional_notes)}</td></tr>" if request.additional_notes else ""}
</table>
<p>Final procurement depends on:</p>
<ul>
  <li>COA, SDS/MSDS, specification sheet, and invoice availability.</li>
  <li>Confirmation of manufacturer, country of origin, grade, purity, and shelf life.</li>
  <li>Regulatory and customs review for the stated destination and intended use.</li>
  <li>Mutually accepted Incoterms, transport mode, payment terms, and delivery schedule.</li>
  <li>Internal approval before any binding purchase order.</li>
</ul>
<p>Sincerely,<br><strong>{escape(company.legal_name or '[Company]')}</strong></p>
<div class="notice">
  This LOI is non-binding. It is not a purchase order, payment authorization, customs
  declaration, or transport instruction.
</div>
"""
        html = _html_shell(subject, company, ref, body_html)
        text = "\n".join(
            [
                _letterhead_text(company, ref, None, "Letter of Intent"),
                "",
                f"To: {request.recipient_name}, {request.recipient_company}",
                f"Product: {request.substance_name}",
                f"CAS: {request.substance_cas}",
                f"Quantity: {request.quantity or 'To be confirmed'}",
                f"Destination: {request.destination_country or 'To be confirmed'}",
                f"Intended lawful use: {request.intended_use or 'Industrial chemical use by qualified personnel'}",
                "",
                "This LOI is non-binding and subject to due diligence, documentation, regulatory review, and internal approval.",
            ]
        )
        return LetterOfIntentResponse(subject=subject, html=html, text=text, pdf_ready=True)

    def generate_po(self, request: PurchaseOrderRequest) -> PurchaseOrderResponse:
        company = request.company or CompanyLetterheadData()
        po_number = request.reference_number or f"PO-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}"
        transport_mode = request.transport_mode.lower()
        suggested = TRANSPORT_INCOTERMS.get(transport_mode, TRANSPORT_INCOTERMS["multimodal"])
        incoterms = request.incoterms.upper()
        if incoterms not in INCOTERMS_RESPONSIBILITY:
            incoterms = suggested[0]
        responsibility = INCOTERMS_RESPONSIBILITY[incoterms]
        subject = f"Purchase Order {po_number} - {request.substance_name} / CAS {request.substance_cas}"

        responsibility_rows = "\n".join(
            f"<tr><td>{escape(key.replace('_', ' ').title())}</td><td>{escape(who)}</td></tr>"
            for key, who in responsibility.items()
        )
        customs_html = f"""
<div class="notice">
  <strong>Customs and end-use information for review</strong><br>
  HS code: {escape(request.hs_code or 'To be confirmed by customs broker')}<br>
  Estimated duty: {escape(request.customs_duty_rate or 'To be confirmed in official tariff database')}<br>
  Lawful-use description: {escape(request.legal_use_description or 'Industrial chemical use by qualified personnel; final wording to be confirmed before customs filing.')}
</div>
"""
        body_html = f"""
<h1>Purchase Order</h1>
<table>
  <tr><th>PO number</th><td>{escape(po_number)}</td></tr>
  <tr><th>Supplier</th><td>{escape(request.supplier_name)}</td></tr>
  <tr><th>Supplier address</th><td>{escape(request.supplier_address or 'To be confirmed')}</td></tr>
  <tr><th>Supplier contact</th><td>{escape(request.supplier_contact or 'To be confirmed')}</td></tr>
  <tr><th>Delivery address</th><td>{escape(request.delivery_address or company.address or 'To be confirmed')}</td></tr>
  <tr><th>Delivery deadline</th><td>{escape(request.delivery_deadline or 'Per agreed schedule')}</td></tr>
</table>
<h2>Order Details</h2>
<table>
  <tr><th>Product</th><td>{escape(request.substance_name)}</td></tr>
  <tr><th>CAS</th><td>{escape(request.substance_cas)}</td></tr>
  <tr><th>Quantity</th><td>{escape(request.quantity)} {escape(request.unit)}</td></tr>
  <tr><th>Unit price</th><td>{escape(request.price_per_unit or 'Per accepted quotation')} {escape(request.currency)}</td></tr>
  <tr><th>Payment terms</th><td>{escape(request.payment_terms)}</td></tr>
  <tr><th>Transport</th><td>{escape(transport_mode)}</td></tr>
  <tr><th>Incoterms</th><td><strong>{escape(incoterms)}</strong></td></tr>
</table>
<h2>Incoterms Responsibility - {escape(incoterms)}</h2>
<table>
  <tr><th>Responsibility</th><th>Party</th></tr>
  {responsibility_rows}
</table>
<p class="small">Suggested Incoterms for {escape(transport_mode)}: {escape(', '.join(suggested))}</p>
{customs_html}
{f"<h2>Special Requirements</h2><p>{escape(request.special_requirements)}</p>" if request.special_requirements else ""}
<div class="notice">
  This PO requires supplier written confirmation and internal buyer approval. It is not an
  authorization to misdeclare product identity, HS code, origin, value, dangerous-goods status,
  or lawful end-use.
</div>
"""
        html = _html_shell(subject, company, po_number, body_html)
        text = "\n".join(
            [
                _letterhead_text(company, po_number, None, "Purchase Order"),
                "",
                f"Supplier: {request.supplier_name}",
                f"Product: {request.substance_name} / CAS {request.substance_cas}",
                f"Quantity: {request.quantity} {request.unit}",
                f"Unit price: {request.price_per_unit or 'Per accepted quotation'} {request.currency}",
                f"Transport: {transport_mode}",
                f"Incoterms: {incoterms}",
                "Responsibilities:",
                *[f"- {key.replace('_', ' ').title()}: {who}" for key, who in responsibility.items()],
                f"HS code: {request.hs_code or 'To be confirmed'}",
                f"Estimated duty: {request.customs_duty_rate or 'To be confirmed'}",
                f"Lawful-use description: {request.legal_use_description or 'To be confirmed'}",
            ]
        )
        return PurchaseOrderResponse(
            po_number=po_number,
            subject=subject,
            html=html,
            text=text,
            incoterms_responsibility=responsibility,
            transport_mode=transport_mode,
            suggested_incoterms=suggested,
            pdf_ready=True,
        )

    def incoterms_guide(self, transport_mode: str) -> IncotermsGuideResponse:
        mode = transport_mode.lower()
        available = TRANSPORT_INCOTERMS.get(mode, TRANSPORT_INCOTERMS["multimodal"])
        return IncotermsGuideResponse(
            transport_mode=mode,
            available_incoterms=available,
            responsibility_matrix={
                incoterm: INCOTERMS_RESPONSIBILITY[incoterm]
                for incoterm in available
                if incoterm in INCOTERMS_RESPONSIBILITY
            },
        )


def _html_shell(
    title: str,
    company: CompanyLetterheadData,
    reference_number: str | None,
    body_html: str,
    date: str | None = None,
) -> str:
    date_text = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    details = [
        company.trading_name,
        company.address,
        company.country,
        f"Reg: {company.registration_number}" if company.registration_number else None,
        f"VAT: {company.vat_number}" if company.vat_number else None,
        f"EORI: {company.eori_number}" if company.eori_number else None,
        company.website,
        company.email,
        company.phone,
    ]
    details_html = " | ".join(escape(item) for item in details if item)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #172033; line-height: 1.5; max-width: 820px; margin: 0 auto; padding: 40px; }}
    .letterhead {{ border-bottom: 3px solid #115e59; padding-bottom: 14px; margin-bottom: 24px; }}
    .company-name {{ font-size: 22px; font-weight: 700; color: #115e59; }}
    .company-details {{ font-size: 11px; color: #64748b; margin-top: 6px; }}
    .reference {{ font-size: 12px; color: #64748b; margin-top: 10px; }}
    h1 {{ font-size: 22px; color: #172033; margin-top: 0; }}
    h2 {{ font-size: 15px; color: #334155; margin-top: 22px; }}
    table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
    th, td {{ border-bottom: 1px solid #e2e8f0; padding: 7px 9px; text-align: left; vertical-align: top; }}
    th {{ width: 210px; background: #f8fafc; color: #475569; font-weight: 600; }}
    .notice {{ background: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #115e59; padding: 10px 12px; margin: 16px 0; font-size: 12px; }}
    .small {{ font-size: 12px; color: #64748b; }}
  </style>
</head>
<body>
  <div class="letterhead">
    <div class="company-name">{escape(company.legal_name or 'Company Name')}</div>
    <div class="company-details">{details_html}</div>
    <div class="reference">Ref: {escape(reference_number or 'N/A')} | Date: {escape(date_text)}</div>
  </div>
  {body_html}
</body>
</html>"""


def _letterhead_text(
    company: CompanyLetterheadData,
    reference_number: str | None,
    date: str | None,
    title: str | None,
) -> str:
    lines = [company.legal_name or "Company Name"]
    for item in [
        company.trading_name,
        company.address,
        company.country,
        company.registration_number,
        company.vat_number,
        company.eori_number,
        company.website,
        company.email,
        company.phone,
    ]:
        if item:
            lines.append(item)
    lines.append(f"Ref: {reference_number or 'N/A'} | Date: {date or datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
    if title:
        lines.append(title)
    return "\n".join(lines)
