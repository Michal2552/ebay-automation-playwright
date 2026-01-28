import logging
from playwright.async_api import Page, Locator

class BasePage:
    logger = logging.getLogger(__name__)
    def __init__(self, page: Page):
        self.page = page



