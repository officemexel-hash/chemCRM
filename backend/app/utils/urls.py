from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if not parsed.scheme:
        parsed = urlparse(f"https://{url.strip()}")
    return parsed.geturl()


def domain_from_url(url: str) -> str:
    return urlparse(normalize_url(url)).netloc.lower()
