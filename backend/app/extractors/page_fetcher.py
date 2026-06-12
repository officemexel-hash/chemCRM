import time
from dataclasses import dataclass

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.extractors.robots import can_fetch


@dataclass(frozen=True)
class FetchedPage:
    url: str
    html: str | None
    status_code: int | None
    fetch_status: str
    captcha_detected: bool = False


class PageFetcher:
    def __init__(self, timeout_seconds: int = 15, delay_seconds: float = 0.5) -> None:
        self.timeout_seconds = timeout_seconds
        self.delay_seconds = delay_seconds
        self._last_fetch_by_domain: dict[str, float] = {}

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def fetch(self, url: str) -> FetchedPage:
        if not can_fetch(url):
            return FetchedPage(url=url, html=None, status_code=None, fetch_status="robots_disallowed")
        self._respect_delay(url)
        try:
            response = httpx.get(
                url,
                timeout=self.timeout_seconds,
                headers={"User-Agent": "ChemicalSourcingRFQCRM/0.1 (+legal B2B procurement)"},
                follow_redirects=True,
            )
        except httpx.HTTPError:
            return FetchedPage(url=url, html=None, status_code=None, fetch_status="fetch_error")
        html = response.text
        return FetchedPage(
            url=str(response.url),
            html=html,
            status_code=response.status_code,
            fetch_status="ok" if response.is_success else "http_error",
            captcha_detected="captcha" in html.lower(),
        )

    def _respect_delay(self, url: str) -> None:
        domain = httpx.URL(url).host or ""
        last = self._last_fetch_by_domain.get(domain, 0)
        elapsed = time.monotonic() - last
        if elapsed < self.delay_seconds:
            time.sleep(self.delay_seconds - elapsed)
        self._last_fetch_by_domain[domain] = time.monotonic()
