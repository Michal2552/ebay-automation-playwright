import logging
from playwright.async_api import Page, Locator

class BasePage:
    logger = logging.getLogger(__name__)
    def __init__(self, page: Page):
        self.page = page

    async def navigate(self, url: str):
        await self.page.goto(url)

    async def click_element(self, selector: str):
        await self.page.wait_for_selector(selector, state="visible")
        await self.page.click(selector)

    async def fill_text(self, selector: str, text: str):
        await self.page.wait_for_selector(selector, state="visible")
        await self.page.fill(selector, text)

    async def get_text(self, selector: str) -> str:
        await self.page.wait_for_selector(selector, state="visible")
        return await self.page.inner_text(selector)

    async def is_element_visible(self, selector: str, timeout: int = 5000) -> bool:
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except:
            return False