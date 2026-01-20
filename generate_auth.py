# generate_auth.py
import asyncio
from playwright.async_api import async_playwright


async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto("https://www.ebay.com/signin")
        await page.wait_for_timeout(60000)
        await context.storage_state(path="auth.json")
        await browser.close()


asyncio.run(run())