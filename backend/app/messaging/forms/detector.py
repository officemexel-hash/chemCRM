from bs4 import BeautifulSoup


FORM_FIELD_NAMES = {"name", "company", "email", "phone", "subject", "message", "product", "cas"}


def detect_contact_forms(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    forms: list[dict] = []
    for form in soup.find_all("form"):
        fields = []
        for field in form.find_all(["input", "textarea", "select"]):
            name = (field.get("name") or field.get("id") or "").lower()
            if any(token in name for token in FORM_FIELD_NAMES):
                fields.append(name)
        forms.append({"action": form.get("action"), "method": form.get("method", "get"), "fields": fields})
    return forms
