import pytest
import json
import os
import logging
import allure
from pages.search_page import SearchPage
from pages.cart_page import CartPage


logger = logging.getLogger(__name__)
def load_test_data():
    """טעינת נתוני בדיקה מקובץ JSON חיצוני"""

    base_path = os.path.dirname(os.path.dirname(__file__))
    json_path = os.path.join(base_path, "data", "test_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.mark.parametrize("data", load_test_data())
@pytest.mark.asyncio

async def test_ebay_full_e2e_flow(page, data):
    # נתונים מה-JSON
    query = data["item_name"]
    max_price = float(data["max_price"])
    limit = int(data["limit"])

    search_page = SearchPage(page)
    cart_page = CartPage(page)
    logger.info(f"Starting E2E Flow for: {query} (Limit: {limit}, Max Price: {max_price})")
    await page.goto("https://www.ebay.com")
    #חיפוש המוצרים וסינון המחיר
    urls = await search_page.search_items_by_name_under_price(query, max_price, limit)
    if not urls:
        logger.warning(f"No products found for {query} under {max_price}. Skipping test.")
        pytest.skip(f"No products found for {query} under {max_price}")
    #הוספת המוצרים לסל
    await cart_page.add_items_to_cart(urls)

    # אימות שסכום הסל לא חורג
    with allure.step("Final Budget Validation"):
        logger.info("Performing final budget verification...")
        await cart_page.assert_cart_total_not_exceeds(max_price, len(urls))

        # צילום מסך סופי עבור הדו"ח
        final_screenshot = await page.screenshot(path="reports/final_cart_status.png")
        allure.attach(
            final_screenshot,
            name="Final Cart State",
            attachment_type=allure.attachment_type.PNG
        )

    logger.info("Test completed successfully!")