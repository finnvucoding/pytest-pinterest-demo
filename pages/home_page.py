from playwright.sync_api import Locator
from config.settings import settings
from core.base_page import BasePage
from core.logger import get_logger
from pages.locators import HomePageLocators as Loc

logger = get_logger()

class HomePage(BasePage):
    """
    Page Object cho Pinterest Home Page.
    """

    def navigate(self):
        """Mở trang chủ và xử lý popup rác (nếu có)"""
        self.open(settings.urls.base_ui)
        self._dismiss_popup_if_present()

    def search_for(self, keyword: str):
        logger.info(f"🔍 Searching for: '{keyword}'")

        # 1. Tìm ô search (Dùng chiến thuật Fallback)
        search_box = self._get_active_search_box()

        # 2. Type với delay (type() hỗ trợ delay, fill() thì không)
        search_box.click()
        self.page.wait_for_timeout(settings.timeouts.TYPING_TIMEOUT)
        search_box.type(keyword, delay=settings.timeouts.TYPING_TIMEOUT)
        logger.info(f"⌨️ Typed '{keyword}' into Search Box")
        
        self.page.wait_for_timeout(settings.timeouts.SHORT13_TIMEOUT)
        search_box.press("Enter")

    # ==================== PRIVATE HELPERS ====================

    def _get_active_search_box(self) -> Locator:
        """
        Tìm ô search. Ưu tiên Technical Selector, Fallback sang Text.
        """
        import re
        
        # Option 1: Dùng data-test-id - Ưu tiên số 1
        box_technical = self.page.locator(Loc.SEARCH_INPUT_SELECTOR)
        if self.is_visible_slow(box_technical, timeout=2000):
            return box_technical

        # Option 2: Dùng name attribute (Fallback 1)
        box_by_name = self.page.locator(Loc.SEARCH_INPUT_BY_NAME)
        if self.is_visible_slow(box_by_name, timeout=2000):
            logger.warning("⚠️ Primary selector failed. Using name attribute fallback.")
            return box_by_name

        # Option 3: Dùng Placeholder regex (Fallback 2 - hỗ trợ đa ngôn ngữ)
        box_label = self.page.get_by_placeholder(re.compile(Loc.SEARCH_PLACEHOLDER_PATTERN, re.IGNORECASE))
        if self.is_visible_slow(box_label, timeout=2000):
            logger.warning("⚠️ Using placeholder pattern fallback.")
            return box_label

        # Fail toàn tập
        self.take_screenshot("search_box_missing")
        raise Exception("❌ Search box not found with any strategy!")

    def _dismiss_popup_if_present(self):
        """Tắt popup quảng cáo/signup nếu xuất hiện"""
        # Giả sử có popup locator
        popup_close = self.page.get_by_label("Close") # Hoặc locator từ file
        
        # Dùng is_visible_slow (timeout ngắn) để check nhanh
        if self.is_visible_slow(popup_close, timeout=3000):
            logger.info("🧹 Dismissing popup...")
            try:
                popup_close.click()
            except Exception:
                pass # Bỏ qua nếu click xịt (popup tự biến mất)