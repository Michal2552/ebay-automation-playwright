import asyncio
import logging
import re
import allure
import os
from .base_page import BasePage
from typing import List, Optional
from playwright.async_api import Page, Locator

logger = logging.getLogger(__name__)
class SearchPage(BasePage):

    SEARCH_INPUT = "input[name='_nkw']"
    MAX_PRICE_INPUT = "input[id*='endParamValue']"
    ITEMS_XPATH = "//li[starts-with(@id, 'item') or contains(@class, 's-item')]"
    NEXT_PAGE_XPATH = "//a[@aria-label='Go to next search page' or contains(@class, 'pagination__next')]"
    async def search_items_by_name_under_price(self, query: str, max_price: float, limit: int = 5)-> List[str]:
        """
        Executes a search and collects product URLs that meet the price criteria.
        Navigates through pages if necessary until the limit is reached.
        """

        with allure.step(f"Search items: {query} (Max: {max_price})"):
            logger.info(f"Searching for '{query}' with price limit {max_price}")
            await self.page.fill(self.SEARCH_INPUT, query)
            await self.page.get_by_role("button", name="Search", exact=True).click()
            await self.page.wait_for_selector(".srp-results", state="visible", timeout=15000)

            await self._apply_price_filter(max_price)

            await self.page.wait_for_selector("xpath=//ul[contains(@class, 'results')]", state="attached", timeout=10000)

        found_urls = []

        while len(found_urls) < limit:
            current_urls = await self._collect_items_from_current_page(max_price, limit - len(found_urls))
            found_urls.extend(current_urls)

            if len(found_urls) < limit:
                if not await self._go_to_next_page():
                    break

        logger.info(f"Search completed. Found {len(found_urls)} valid items.")
        return found_urls

    async def _apply_price_filter(self, max_price: float):
        """Applies the maximum price filter using eBay's sidebar/header input."""
        try:

           max_input = self.page.locator(self.MAX_PRICE_INPUT).first
           await self.page.wait_for_timeout(2000)
           if await max_input.is_visible():

              logger.info(f"Applying price filter: {max_price}")

              await max_input.fill(str(max_price))
              await self.page.wait_for_timeout(2000)
              await max_input.press("Enter")
              await self.page.wait_for_timeout(2000)
              await self.page.get_by_test_id("mainContent").get_by_role("link", name="Buy It Now").click()
              await self.page.wait_for_selector("xpath=//ul[contains(@class, 'results')]", state="attached", timeout=10000)
           else:

              logger.warning("Price filter input not found, proceeding with manual filtration.")

        except Exception as e:
            logger.error(f"Failed to apply price filter: {e}")

    async def _collect_items_from_current_page(self, max_price: float, limit: int) -> List[str]:
        """Parses the current results page for items below max_price."""
        urls = []
        items = await self.page.locator(f"xpath={self.ITEMS_XPATH}").all()

        for item in items:
            if len(urls) >= limit:
                break

            try:
                price_text = await item.locator("xpath=.//*[contains(@class, 'price')]").first.inner_text()
                current_price = self._extract_price(price_text)

                if current_price and current_price <= max_price:
                    link = item.locator("xpath=.//a[contains(@class, 'link')]").first
                    url = await link.get_attribute("href")
                    if url and "itm" in url:
                        urls.append(url)
            except:
                continue
        return urls

    async def _go_to_next_page(self) -> bool:
        """Attempts to click the 'Next' pagination button."""
        next_button = self.page.locator(f"xpath={self.NEXT_PAGE_XPATH}").first
        if await next_button.is_visible():
            logger.info("Navigating to the next results page...")
            await next_button.click()
            await self.page.wait_for_timeout(3000)
            return True
        return False

    def _extract_price(self, text: str) -> float:
        """Utility to convert price strings (e.g., '$1,200.50') to float."""
        clean_text = text.replace(",", "")
        matches = re.findall(r'\d+\.?\d*', clean_text)
        return float(matches[0]) if matches else None
