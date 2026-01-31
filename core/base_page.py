from playwright.sync_api import Locator, Page, expect
from config import settings
from core.logger import log

logger = log()

class BasePage:
    def __init__(self, page: Page):
        self.page = page

    # ==================== NAVIGATION ====================

    def open(self, url: str):
        logger.info(f"🌍 Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded")

    def refresh(self):
        logger.info("🔄 Refreshing page...")
        self.page.reload(wait_until="domcontentloaded")

    # ==================== ACTIONS ====================
    
    def click(self, locator: Locator, description: str = "element", **kwargs):
        """
        Wrapper cho click với log chi tiết.
        Usage: self.click(self.btn_login, "Login Button", force=True)
        """
        logger.info(f"🖱️ Clicking on '{description}'")
        try:
            locator.click(**kwargs)
        except Exception as e:
            logger.error(f"❌ Failed to click '{description}': {str(e)}")
            self.take_screenshot(f"fail_click_{description}")
            raise e

    def fill(self, locator: Locator, text: str, description: str = "field", **kwargs):
        """Wrapper cho fill (tự động clear mặc định của Playwright)"""
        logger.info(f"⌨️ Typing '{text}' into '{description}'")
        locator.fill(text, **kwargs)

    def get_text(self, locator: Locator, description: str = None) -> str:
        text = locator.text_content() or ""
        desc = description or "element"
        logger.debug(f"👀 Read text from '{desc}': '{text.strip()}'")
        return text.strip()

    # ==================== WAIT STRATEGIES ====================

    def wait_for_visible(self, locator: Locator, description: str = "element", timeout: int = 10000):
        logger.debug(f"⏳ Waiting for '{description}' to be visible...")
        expect(locator).to_be_visible(timeout=timeout)

    def wait_for_url(self, partial_url: str):
        logger.info(f"⏳ Waiting for URL containing: '{partial_url}'")
        self.page.wait_for_url(f"**{partial_url}**")

    # ==================== STATE CHECKS ====================

    def is_visible(self, locator: Locator) -> bool:
        """Kiểm tra tức thì (Instant check), không chờ đợi"""
        return locator.is_visible()

    def is_visible_slow(self, locator: Locator, timeout: int = 3000) -> bool:
        """Chờ một chút xem có hiện ra không (Dùng cho element load chậm)"""
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False

    # ==================== UTILS ====================

    def take_screenshot(self, name: str):
        try:
            path = f"screenshots/{name+settings.get_current_timestamp()}.png"
            self.page.screenshot(path=path, full_page=True)
            logger.info(f"📸 Screenshot saved: {path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not take screenshot: {e}")