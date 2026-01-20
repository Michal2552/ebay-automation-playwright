import pytest
import pytest_asyncio
import os
import logging
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

@pytest_asyncio.fixture(scope="function")
async def page():
    """
        Fixture that initializes the browser, sets up a stealth context,
        manages tracing, and ensures proper cleanup after each test.
        """

    async with async_playwright() as p:
        logger.info("  Launching Chromium browser...")
        browser = await p.chromium.launch(headless=False, args=[
            "--start-maximized",
            "--disable-blink-features=AutomationControlled"
        ])

        storage_path = "auth.json"
        storage_state = storage_path if os.path.exists(storage_path) else None
        if storage_state:
            logger.info(f" Using existing session state from {storage_path}")

        context = await browser.new_context(
            no_viewport=True,
            storage_state=storage_state,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        os.makedirs("reports", exist_ok=True)
        await context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = await context.new_page()
        yield page

        logger.info(" Test finished. Cleaning up and saving trace...")

        try:
            await context.tracing.stop(path="reports/trace.zip")
            await page.close()
            await context.close()
            await browser.close()

        except Exception as e:
            logger.error(f"Error during browser teardown: {e}")