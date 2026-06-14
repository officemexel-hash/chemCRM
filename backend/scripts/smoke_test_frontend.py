"""Frontend smoke test — clicks through all dashboard views via Playwright.
Usage: python scripts/smoke_test_frontend.py [--base-url http://localhost:3000]
"""
import asyncio
import sys
import time

BASE_URL = "http://localhost:3000"
SCREENSHOTS_DIR = "storage/screenshots"

VIEWS = [
    ("dashboard", "Dashboard"),
    ("import", "Import CAS"),
    ("sourcing", "Sourcing"),
    ("intelligence", "Intelligence"),
    ("documents", "Docs"),
    ("substances", "Substances"),
    ("discovery", "Discovery"),
    ("suppliers", "Suppliers"),
    ("campaigns", "RFQ"),
    ("inbox", "Inbox"),
    ("quotes", "Quotes"),
    ("tariff", "Tariff"),
    ("reports", "Reports"),
    ("tasks", "Tasks"),
    ("rebrand", "Rebrand"),
    ("settings", "Settings"),
]


async def smoke_test() -> int:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
        return 1

    import os
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    failures = 0
    print(f"Smoke test: {BASE_URL}")
    print(f"Screenshots: {SCREENSHOTS_DIR}/")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1440, "height": 900})

        try:
            # Load the main page
            start = time.time()
            resp = await page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
            load_time = time.time() - start
            if resp and resp.ok:
                print(f"  Page loaded in {load_time:.1f}s (HTTP {resp.status})")
            else:
                print(f"  FAIL: HTTP {resp.status if resp else 'no response'}")
                failures += 1
                return failures

            await page.wait_for_timeout(500)

            # Take initial screenshot
            await page.screenshot(path=f"{SCREENSHOTS_DIR}/01_dashboard.png")
            print("  Screenshot: dashboard")

            # Click through each tab and take a screenshot
            for idx, (tab_id, tab_label) in enumerate(VIEWS[1:], start=2):
                try:
                    # Find and click the tab button by its title text
                    tab_btn = page.locator(f'button[title="{tab_label}"]')
                    if await tab_btn.count() == 0:
                        # Try clicking by visible text
                        tab_btn = page.get_by_role("button", name=tab_label)
                    await tab_btn.click()
                    await page.wait_for_timeout(600)

                    filename = f"{SCREENSHOTS_DIR}/{idx:02d}_{tab_id}.png"
                    await page.screenshot(path=filename)
                    print(f"  Screenshot: {tab_id} ({tab_label})")
                except Exception as e:
                    print(f"  FAIL: {tab_id} ({tab_label}) — {e}")
                    failures += 1

            # Test dialogs
            print("  Testing dialogs...")

            # 1. Add Substance dialog
            try:
                await page.goto(BASE_URL, wait_until="networkidle", timeout=10000)
                await page.wait_for_timeout(500)
                # Click Substances tab first
                substances_btn = page.get_by_role("button", name="Substances")
                await substances_btn.click()
                await page.wait_for_timeout(400)
                # Click "Add CAS" button
                add_cas_btn = page.get_by_role("button", name="Add CAS")
                await add_cas_btn.click()
                await page.wait_for_timeout(400)
                # Verify dialog is visible
                dialog = page.locator("text=Add Substance")
                if await dialog.count() > 0:
                    print("  Dialog: Add Substance OK")
                    await page.screenshot(path=f"{SCREENSHOTS_DIR}/dialog_add_substance.png")
                    # Close dialog — click the backdrop
                    await page.locator(".fixed.inset-0.z-50").click(position={"x": 10, "y": 10})
                    await page.wait_for_timeout(300)
                else:
                    print("  FAIL: Add Substance dialog not shown")
                    failures += 1
            except Exception as e:
                print(f"  FAIL: Add Substance dialog — {e}")
                failures += 1

            # 2. Add Supplier dialog
            try:
                suppliers_btn = page.get_by_role("button", name="Suppliers")
                await suppliers_btn.click()
                await page.wait_for_timeout(400)
                add_sup_btn = page.get_by_role("button", name="Add Supplier")
                await add_sup_btn.click()
                await page.wait_for_timeout(400)
                dialog2 = page.locator("text=Add Supplier")
                if await dialog2.count() > 0:
                    print("  Dialog: Add Supplier OK")
                    await page.locator(".fixed.inset-0.z-50").click(position={"x": 10, "y": 10})
                    await page.wait_for_timeout(300)
                else:
                    print("  FAIL: Add Supplier dialog not shown")
                    failures += 1
            except Exception as e:
                print(f"  FAIL: Add Supplier dialog — {e}")
                failures += 1

            # 3. Settings view
            try:
                settings_btn = page.get_by_role("button", name="Settings")
                await settings_btn.click()
                await page.wait_for_timeout(400)
                print("  View: Settings loaded OK")
            except Exception as e:
                print(f"  FAIL: Settings — {e}")
                failures += 1

        finally:
            await browser.close()

    print(f"\nResult: {failures} failures out of {len(VIEWS)} views + dialogs")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].startswith("--base-url"):
        BASE_URL = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].split("=", 1)[-1]
    exit(asyncio.run(smoke_test()))
