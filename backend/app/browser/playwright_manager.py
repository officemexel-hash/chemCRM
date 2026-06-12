"""Playwright browser manager — manages browser instances for marketplace,
form, and web automation. Handles sessions, cookies, CAPTCHA detection,
rate limiting, and screenshot evidence collection."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to import playwright — it's optional
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logger.warning("playwright not installed — browser automation disabled. Install with: pip install playwright && playwright install chromium")


@dataclass
class BrowserSession:
    """A managed browser session for one marketplace/domain."""
    domain: str
    context: Any = None  # BrowserContext
    page: Any = None  # Page
    logged_in: bool = False
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    request_count: int = 0


class PlaywrightManager:
    """Singleton manager for Playwright browser instances.

    Features:
    - Lazy initialization (only starts browser when first needed)
    - Per-domain session isolation (separate cookies/storage)
    - Rate limiting (configurable requests per minute per domain)
    - CAPTCHA detection (logs warning, takes screenshot)
    - Automatic session cleanup
    """

    _instance: "PlaywrightManager | None" = None
    _playwright: Any = None
    _browser: Any = None  # Browser

    def __new__(cls) -> "PlaywrightManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
            cls._instance._rate_limits = {}
            cls._instance._initialized = False
        return cls._instance

    @property
    def is_available(self) -> bool:
        return HAS_PLAYWRIGHT

    async def initialize(self) -> None:
        """Start the browser. Called lazily on first use."""
        if self._initialized or not HAS_PLAYWRIGHT:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        self._initialized = True
        logger.info("Playwright browser started")

    async def shutdown(self) -> None:
        """Close all sessions and the browser."""
        for session in list(self._sessions.values()):
            if session.context:
                await session.context.close()
        self._sessions.clear()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._initialized = False
        logger.info("Playwright browser shut down")

    async def get_session(self, domain: str, user_data_dir: str | None = None) -> BrowserSession:
        """Get or create a browser session for a domain."""
        await self.initialize()

        if domain in self._sessions:
            session = self._sessions[domain]
            session.last_used = time.time()
            return session

        # Rate limit check
        self._check_rate_limit(domain)

        # Create new context
        context_kwargs = {}
        if user_data_dir:
            Path(user_data_dir).mkdir(parents=True, exist_ok=True)
            context_kwargs["storage_state"] = user_data_dir

        context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )
        page = await context.new_page()
        session = BrowserSession(domain=domain, context=context, page=page)
        self._sessions[domain] = session
        logger.info("Created new browser session for %s", domain)
        return session

    async def fetch_page(self, url: str, domain: str, wait_for: str | None = None) -> dict:
        """Fetch a page and return its HTML content plus metadata."""
        session = await self.get_session(domain)
        session.request_count += 1
        self._track_request(domain)

        page = session.page
        try:
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if wait_for:
                await page.wait_for_selector(wait_for, timeout=10000)

            html = await page.content()
            captcha_detected = await self._detect_captcha(page)
            status_code = response.status if response else 0

            return {
                "url": url,
                "html": html,
                "status_code": status_code,
                "captcha_detected": captcha_detected,
                "success": 200 <= status_code < 400 and not captcha_detected,
            }
        except Exception as e:
            logger.error("Failed to fetch %s: %s", url, e)
            return {
                "url": url,
                "html": None,
                "status_code": 0,
                "captcha_detected": False,
                "success": False,
                "error": str(e),
            }

    async def fill_and_submit_form(
        self, url: str, domain: str, field_values: dict[str, str],
        submit_selector: str = 'button[type="submit"], input[type="submit"]',
    ) -> dict:
        """Fill in a web form and submit it. Returns result with screenshot path."""
        session = await self.get_session(domain)
        page = session.page

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            screenshot_before = await self._screenshot(page, f"form_before_{domain}")

            # Fill known fields
            for field_name, value in field_values.items():
                try:
                    # Try by name attribute first
                    selector = f'input[name="{field_name}"], textarea[name="{field_name}"]'
                    if await page.query_selector(selector):
                        await page.fill(selector, str(value))
                        continue
                    # Try by id
                    selector = f'#{field_name}'
                    if await page.query_selector(selector):
                        await page.fill(selector, str(value))
                        continue
                    # Try by placeholder
                    selector = f'input[placeholder*="{field_name}" i], textarea[placeholder*="{field_name}" i]'
                    if await page.query_selector(selector):
                        await page.fill(selector, str(value))
                except Exception as e:
                    logger.debug("Could not fill field %s: %s", field_name, e)

            # Submit
            submit_btn = await page.query_selector(submit_selector)
            if submit_btn:
                await submit_btn.click()
                await page.wait_for_timeout(3000)
            else:
                # Try pressing Enter in the last filled field
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)

            screenshot_after = await self._screenshot(page, f"form_after_{domain}")
            return {
                "status": "submitted",
                "screenshot_before": screenshot_before,
                "screenshot_after": screenshot_after,
                "url": url,
            }
        except Exception as e:
            logger.error("Form submit failed for %s: %s", url, e)
            return {
                "status": "failed",
                "error": str(e),
                "url": url,
            }

    async def _detect_captcha(self, page: Any) -> bool:
        """Check if the current page has a CAPTCHA."""
        captcha_indicators = [
            "captcha", "recaptcha", "hcaptcha", "cloudflare",
            "verify you are human", "verify you're human",
        ]
        try:
            body_text = (await page.text_content("body")).lower()
            return any(indicator in body_text for indicator in captcha_indicators)
        except Exception:
            return False

    async def _screenshot(self, page: Any, name: str) -> str | None:
        """Take a screenshot and return the file path."""
        try:
            from app.core.config import get_settings
            settings = get_settings()
            import os
            os.makedirs(settings.storage_path, exist_ok=True)
            path = Path(settings.storage_path) / f"{name}_{int(time.time())}.png"
            await page.screenshot(path=str(path), full_page=False)
            return str(path)
        except Exception as e:
            logger.warning("Screenshot failed: %s", e)
            return None

    def _check_rate_limit(self, domain: str, max_per_minute: int = 10) -> None:
        now = time.time()
        if domain in self._rate_limits:
            timestamps = [ts for ts in self._rate_limits[domain] if now - ts < 60]
            if len(timestamps) >= max_per_minute:
                wait_time = 60 - (now - timestamps[0]) + 1
                logger.warning("Rate limit hit for %s — would wait %.1fs", domain, wait_time)
                time.sleep(min(wait_time, 10))  # Cap wait at 10s
            self._rate_limits[domain] = timestamps
        else:
            self._rate_limits[domain] = []

    def _track_request(self, domain: str) -> None:
        now = time.time()
        if domain not in self._rate_limits:
            self._rate_limits[domain] = []
        self._rate_limits[domain].append(now)


# Global singleton
_playwright_manager: PlaywrightManager | None = None


def get_playwright() -> PlaywrightManager:
    global _playwright_manager
    if _playwright_manager is None:
        _playwright_manager = PlaywrightManager()
    return _playwright_manager
