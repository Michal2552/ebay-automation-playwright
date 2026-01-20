import random
import re
import allure
import os
import logging
from .base_page import BasePage
logger = logging.getLogger(__name__)

class CartPage(BasePage):
    SUMMARY_PANEL = "#RightSummaryPanel"
    ATC_BUTTON = "[data-testid='x-atc-action'] [data-testid='ux-call-to-action']"
    SUCCESS_TEXT = "Added to cart"
    CLOSE_DIALOG = "button[name='Close dialog'], [aria-label='Close dialog']"
    SUBTOTAL_LABEL = "[data-test-id='subtotal-value']"

    async def add_items_to_cart(self, urls: list):
        os.makedirs("screenshots", exist_ok=True)

        for index, url in enumerate(urls):
            with allure.step(f"Processing item {index + 1}/{len(urls)}"):
                new_page = await self.page.context.new_page()
                try:
                    logger.info(f"[{index + 1}] Opening product: {url[:60]}...")
                    await new_page.goto(url, wait_until="load", timeout=60000)
                    await new_page.wait_for_timeout(2000)

                    await self._handle_variations_in_panel(new_page)
                    await self._click_add_to_cart(index, new_page)

                    await new_page.close()
                except Exception as e:
                    logger.error(f" Error adding item {index + 1}: {str(e)}")
                    await new_page.screenshot(path=f"reports/error_item_{index + 1}.png")
                    await new_page.close()
    async def _handle_variations_in_panel(self, page):
        panel = page.locator(self.SUMMARY_PANEL)
        for _ in range(3):
            select_buttons = panel.get_by_role("button").filter(has_text=re.compile("Select", re.I))
            target_button = None
            count = await select_buttons.count()
            for i in range(count):
                btn = select_buttons.nth(i)
                if await btn.is_visible():
                    target_button = btn
                    break

            if not target_button:
                break

            button_text = await target_button.inner_text()
            logger.info(f"Opening selection menu: {button_text}")
            await target_button.click()
            await page.wait_for_timeout(1000)

            all_options = await page.get_by_role("option").all()
            valid_options = []

            for opt in all_options:
                if await opt.is_visible():
                    text = await opt.inner_text()
                    is_disabled = await opt.get_attribute("aria-disabled") == "true"
                    if text and "Select" not in text and not is_disabled:
                        valid_options.append(opt)

            if valid_options:
                choice = random.choice(valid_options)
                choice_text = await choice.inner_text()
                logger.info(f"Randomly selected option: {choice_text}")
                await choice.click()
                await page.wait_for_timeout(2000)
            else:
                logger.warning("No valid options found. Closing menu.")
                await page.keyboard.press("Escape")
                break

    async def _click_add_to_cart(self, index, page):
        atc_btn = page.locator(self.ATC_BUTTON).first
        await atc_btn.click()
        logger.info(f"Clicked 'Add to cart' for item {index + 1}. Checking for CAPTCHA...")

        # בדיקת קאפצ'ה
        captcha = page.locator("iframe[title*='reCAPTCHA']").first
        if await captcha.is_visible(timeout=3000):
            logger.warning(" CAPTCHA detected! Waiting for manual solution...")
            await captcha.wait_for(state="hidden", timeout=300000)
            await atc_btn.click()

        success_found = False
        indicator = page.get_by_text(self.SUCCESS_TEXT, exact=False)

        try:
            await indicator.wait_for(state="visible", timeout=10000)
            logger.info(f" Confirmation found: '{self.SUCCESS_TEXT}' visible on screen.")
            success_found = True
            png_bytes = await page.screenshot()
            file_path = f"reports/log_item_{index + 1}_added.png"
            with open(file_path, "wb") as f:
                f.write(png_bytes)

            allure.attach(
                png_bytes,
                name=f"Log - Item {index + 1} Added",
                attachment_type=allure.attachment_type.PNG
            )
            logger.info(f"Evidence screenshot saved: {file_path}")
            await page.wait_for_timeout(2000)

        except Exception:
            logger.error(f" Visual confirmation not found for item {index + 1}")

        # סגירת הדיאלוג
        close_btn = page.locator(self.CLOSE_DIALOG).first
        if await close_btn.is_visible():
            await close_btn.click()
            logger.info("Popup closed via button.")
        else:
            await page.keyboard.press("Escape")
            logger.info("Popup closed via Escape key.")

        if not success_found:
            raise Exception(f"Failed to verify 'Add to cart' for item {index + 1}")

    async def assert_cart_total_not_exceeds(self, budget_per_item: float, items_count: int):
        with allure.step("Validating cart total against budget"):
            logger.info("Navigating to cart for price validation...")
            await self.page.goto("https://cart.ebay.com", wait_until="networkidle")

            possible_selectors = [
                "[data-test-id='subtotal-value']",
                ".font-title-3",
                "div:has-text('Subtotal') + div",
                ".atc-subtotal span"
            ]

            total_text = ""
            for selector in possible_selectors:
                element = self.page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    total_text = await element.inner_text()
                    if total_text: break

            if not total_text:
                logger.warning("Selector-based price fetch failed, trying regex search...")
                total_text = await self.page.get_by_text(re.compile(r'\$\d+\.\d+')).first.inner_text()

            actual_price = float(re.sub(r'[^\d.]', '', total_text))
            threshold = budget_per_item * items_count

            logger.info(f"Cart Total: {actual_price:.2f} | Allowed Threshold: {threshold:.2f}")

            await self.page.screenshot(path="reports/final_cart_status.png")

            if actual_price > threshold:
                logger.error(f"Budget exceeded! Over by {actual_price - threshold:.2f}")
            else:
                logger.info(f"Budget OK. Remaining margin: {threshold - actual_price:.2f}")

            assert actual_price <= threshold, f"Budget Breach! {actual_price} > {threshold}"
