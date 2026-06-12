"""Document Rebrander — takes supplier MSDS/SDS and COA documents
and regenerates them on the company's own letterhead.

This is standard practice in chemical distribution (private labeling):
the distributor rebrands supplier documentation with their own company
details so the end customer sees the distributor's branding, not the
original manufacturer's.
"""

import io
import logging
import os
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import new_uuid
from app.db.models.document import GeneratedDocument
from app.services.app_settings import AppSettingsService
from app.services.audit_log import AuditLogService

logger = logging.getLogger(__name__)


class DocumentRebrander:
    """Rebrand MSDS/SDS and COA documents onto the distributor's company letterhead."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = AppSettingsService(db).get()
        self.company = self.settings.company
        self.sender = self.settings.sender

    def rebrand_pdf(self, input_pdf_bytes: bytes, doc_type: str, substance_name: str = "", cas: str = "") -> GeneratedDocument:
        """Take a supplier PDF and regenerate it on company letterhead."""
        pages_text = self._extract_text_from_pdf(input_pdf_bytes)
        cleaned_pages = self._remove_supplier_info(pages_text)
        html = self._build_rebranded_html(cleaned_pages, doc_type, substance_name, cas)
        return self._save_rebranded(html, doc_type, substance_name, cas)

    def rebrand_from_text(self, text: str, doc_type: str, substance_name: str = "", cas: str = "") -> GeneratedDocument:
        """Rebrand from raw text content."""
        pages = [text]
        cleaned_pages = self._remove_supplier_info(pages)
        html = self._build_rebranded_html(cleaned_pages, doc_type, substance_name, cas)
        return self._save_rebranded(html, doc_type, substance_name, cas)

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> list[str]:
        try:
            from pypdf import PdfReader
        except ImportError:
            logger.warning("pypdf not installed")
            return ["[PDF content - install pypdf for full extraction]"]
        pages: list[str] = []
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                text = page.extract_text() or ""
                pages.append(text)
        except Exception as e:
            logger.error("PDF extraction error: %s", e)
            pages.append(f"[Error: {e}]")
        return pages

    def _remove_supplier_info(self, pages: list[str]) -> list[str]:
        our_company = (self.company.legal_name or "").lower()
        our_address = (self.company.address or "").lower()
        our_phone = self.sender.phone or ""
        our_email = str(self.sender.email or "").lower()

        cleaned: list[str] = []
        for page_text in pages:
            lines = page_text.split("\n")
            filtered_lines: list[str] = []
            skip_next = False
            for line in lines:
                stripped = line.strip()
                lower = stripped.lower()
                if skip_next:
                    skip_next = False
                    if self._is_address_line(stripped) and our_company not in lower:
                        continue
                if self._is_manufacturer_header(lower):
                    skip_next = True
                    continue
                if self._is_address_line(stripped) and our_company not in lower and our_address not in lower:
                    continue
                if self._is_phone_line(lower) and our_phone not in stripped:
                    continue
                if self._is_email_line(lower) and our_email not in lower:
                    continue
                if self._is_website_line(lower):
                    continue
                filtered_lines.append(stripped)
            cleaned.append("\n".join(filtered_lines))
        return cleaned

    def _is_manufacturer_header(self, lower_line: str) -> bool:
        markers = ["manufacturer:", "supplier:", "prepared by:", "distributed by:",
                   "manufacturer:", "company name:", "producent:", "dostawca:", "hersteller:"]
        return any(m in lower_line for m in markers)

    def _is_address_line(self, line: str) -> bool:
        address_words = ["str.", "straße", "street", "ave", "blvd", "road", "ul.", "ulica"]
        has_addr = any(w in line.lower() for w in address_words)
        has_zip = bool(re.search(r"\b\d{2,5}\s+[A-Z]{2,4}", line))
        return has_addr or has_zip

    def _is_phone_line(self, lower_line: str) -> bool:
        return bool(re.search(r"(tel[.ephone]*|fax|phone)[\s:]", lower_line))

    def _is_email_line(self, lower_line: str) -> bool:
        return "@" in lower_line and ("email" in lower_line or "e-mail" in lower_line or
               bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", lower_line)))

    def _is_website_line(self, lower_line: str) -> bool:
        return bool(re.search(r"(https?://|www\.)", lower_line))

    def _build_rebranded_html(self, pages: list[str], doc_type: str, substance_name: str, cas: str) -> str:
        company = self.company
        sender = self.sender
        doc_title = "SAFETY DATA SHEET" if doc_type in ("msds", "sds") else "CERTIFICATE OF ANALYSIS"
        date_str = datetime.now().strftime("%Y-%m-%d")

        details = []
        if company.address: details.append(company.address)
        if company.country: details.append(company.country)
        if company.registration_number: details.append(f"Reg: {company.registration_number}")
        if company.vat_number: details.append(f"VAT: {company.vat_number}")
        if company.eori_number: details.append(f"EORI: {company.eori_number}")
        company_details = " | ".join(details)

        contact_parts = []
        if sender.name: contact_parts.append(sender.name)
        if sender.email: contact_parts.append(str(sender.email))
        if sender.phone: contact_parts.append(sender.phone)
        contact_line = " | ".join(contact_parts)

        pages_html = ""
        for i, page_text in enumerate(pages):
            safe = page_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>\n")
            pages_html += f'<div class="page{" first-page" if i == 0 else ""}"><div class="page-content">{safe}</div></div>'

        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{doc_title} - {substance_name or 'Document'}</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #1a1a1a; font-size: 9.5pt; line-height: 1.5; margin: 0; padding: 0; }}
  .letterhead {{ border-bottom: 3px solid #1a3a5c; padding-bottom: 12px; margin-bottom: 16px; }}
  .company-name {{ font-size: 16pt; font-weight: bold; color: #1a3a5c; }}
  .company-details {{ font-size: 8.5pt; color: #555; margin-top: 4px; }}
  .doc-header {{ text-align: center; margin-bottom: 16px; padding: 8px; background: #f0f4f8; border: 1px solid #ccc; }}
  .doc-title {{ font-size: 14pt; font-weight: bold; color: #1a3a5c; }}
  .doc-meta {{ font-size: 8.5pt; color: #555; margin-top: 4px; }}
  .page {{ page-break-before: always; }}
  .page.first-page {{ page-break-before: auto; }}
  .page-content {{ white-space: pre-wrap; word-wrap: break-word; font-size: 9pt; line-height: 1.6; }}
  .footer {{ margin-top: 30px; border-top: 1px solid #ccc; padding-top: 8px; font-size: 8pt; color: #888; text-align: center; }}
</style></head>
<body>
<div class="letterhead">
  <div class="company-name">{company.legal_name or 'Company Name'}</div>
  <div class="company-details">{company_details}</div>
</div>
<div class="doc-header">
  <div class="doc-title">{doc_title}</div>
  <div class="doc-meta">
    {"Product: " + substance_name if substance_name else ""}
    {" | CAS: " + cas if cas else ""}
    {" | Date: " + date_str}
  </div>
</div>
{pages_html}
<div class="footer">
  {contact_line}
  <br>This document has been rebranded for distribution. All chemical and safety data is reproduced from the original manufacturer's documentation.
</div>
</body></html>"""

    def _save_rebranded(self, html: str, doc_type: str, substance_name: str, cas: str) -> GeneratedDocument:
        settings = get_settings()
        os.makedirs(settings.storage_path, exist_ok=True)
        doc = GeneratedDocument(
            id=new_uuid(),
            doc_type=f"rebranded_{doc_type}",
            substance_id=None,
            status="generated",
            parameters={"original_doc_type": doc_type, "substance_name": substance_name,
                        "cas": cas, "rebrand_date": datetime.now().isoformat()},
        )
        filename = f"rebranded_{doc_type}_{doc.id[:8]}.pdf"
        filepath = os.path.join(settings.storage_path, filename)
        try:
            from weasyprint import HTML
            HTML(string=html).write_pdf(filepath)
            doc.file_path = filepath
            doc.file_size_bytes = os.path.getsize(filepath)
        except ImportError:
            html_path = filepath.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            doc.file_path = html_path
            doc.file_size_bytes = os.path.getsize(html_path)
            logger.warning("weasyprint not available, saved as HTML")
        except Exception as e:
            logger.error("PDF error: %s", e)
            html_path = filepath.replace(".pdf", ".html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html)
            doc.file_path = html_path
            doc.file_size_bytes = os.path.getsize(html_path)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        AuditLogService(self.db).log("document_rebranded", "generated_document", doc.id,
                                     {"doc_type": doc_type, "substance_name": substance_name, "cas": cas})
        return doc
