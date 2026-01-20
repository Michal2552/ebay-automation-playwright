import os
from .base_page import BasePage

class LoginPage(BasePage):
    USER_INPUT = "#userid"
    PASS_INPUT = "#pass"
    CONTINUE_BTN = "#signin-continue-btn"
    SIGNIN_BTN = "#sgnBt"

    async def login(self, username, password, state_path="auth.json"):
        await self.page.goto("https://www.ebay.com/signin")
        await self.page.fill(self.USER_INPUT, username)
        await self.page.click(self.CONTINUE_BTN)
        await self.page.wait_for_selector(self.PASS_INPUT, state="visible")
        await self.page.fill(self.PASS_INPUT, password)
        await self.page.click(self.SIGNIN_BTN)
        await self.page.wait_for_url("https://www.ebay.com/**", timeout=60000)
        await self.page.context.storage_state(path=state_path)
