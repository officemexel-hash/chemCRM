import re
from dataclasses import dataclass

from bs4 import BeautifulSoup


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?:\+\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,5}\d")
CAS_RE = re.compile(r"\b\d{2,7}-\d{2}-\d\b")
MESSENGER_RE = re.compile(r"\b(whatsapp|telegram|wechat|threema|signal|wickr)\b", re.I)


@dataclass(frozen=True)
class ExtractedContact:
    channel: str
    value: str
    source_url: str
    evidence_text: str
    consent_status: str = "unknown"


class ContactExtractor:
    def extract(self, html: str, source_url: str) -> list[ExtractedContact]:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(" ", strip=True)
        contacts: list[ExtractedContact] = []

        for email in sorted(set(EMAIL_RE.findall(text))):
            if _looks_personal(email):
                continue
            contacts.append(
                ExtractedContact("email", email, source_url, _evidence_around(text, email))
            )
        for phone in sorted(set(PHONE_RE.findall(text)))[:5]:
            contacts.append(
                ExtractedContact("phone", phone.strip(), source_url, _evidence_around(text, phone))
            )
        for form in soup.find_all("form"):
            action = form.get("action") or source_url
            contacts.append(
                ExtractedContact("form", action, source_url, "HTML contact/inquiry form found on source page.")
            )
        for match in MESSENGER_RE.finditer(text):
            channel = match.group(1).lower()
            contacts.append(
                ExtractedContact(
                    channel,
                    channel,
                    source_url,
                    _evidence_around(text, match.group(0)),
                    consent_status="public_business_contact",
                )
            )
        return contacts

    def extract_products(self, html: str) -> list[dict]:
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        return [{"listed_cas": cas, "evidence_text": _evidence_around(text, cas)} for cas in set(CAS_RE.findall(text))]


def _evidence_around(text: str, needle: str, radius: int = 90) -> str:
    index = text.lower().find(needle.lower())
    if index == -1:
        return text[:180]
    return text[max(0, index - radius) : index + len(needle) + radius].strip()


def _looks_personal(email: str) -> bool:
    local = email.split("@", 1)[0].lower()
    return any(token in local for token in ["gmail", "hotmail"]) or len(local.split(".")) >= 3
