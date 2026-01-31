import pytest
import urllib.parse
from playwright.sync_api import expect
import re

from config.settings import settings
from core.logger import get_logger

# Page Objects (Tự động inject qua Fixture conftest)
from pages.home_page import HomePage
from pages.search_result_page import SearchResultPage
from pages.login_page import LoginPage

logger = get_logger()

# ==================== TEST DATA ====================

SEARCH_KEYWORDS = [
    pytest.param("Minimalist Decor", id="minimalist_decor"),
    pytest.param("Cyberpunk Art", id="cyberpunk_art"),
]

# ==================== TEST SUITE ====================

@pytest.mark.smoke
class TestPinterestSearch:

    @pytest.fixture(scope="function", autouse=True)
    def setup_authenticated_state(self, login_page: LoginPage):
        logger.info("[SETUP] 🔐 Ensuring authenticated state...")
        login_page.navigate()
        
        login_page.login(settings.credentials.email, settings.credentials.password)
            
        yield
        # Teardown (nếu cần)

    @pytest.mark.parametrize("keyword", SEARCH_KEYWORDS)
    def test_search_flow(
        self,
        home_page: HomePage,
        search_result_page: SearchResultPage,
        keyword: str,
    ):
        home_page.search_for(keyword)

        actual_count = search_result_page.wait_for_results(min_count=1)
        
        assert actual_count > 0, f"Expected pins for '{keyword}', found 0"
        logger.info(f"[TEST] ✅ Found {actual_count} pins for '{keyword}'")

        encoded_keyword = urllib.parse.quote(keyword)
        current_url = search_result_page.page.url
        
        assert encoded_keyword.lower() in current_url.lower() or \
               keyword.replace(" ", "-").lower() in current_url.lower(), \
               f"URL mismatch. Keyword: {keyword}, URL: {current_url}"

    def test_homepage_layout(self, home_page: HomePage):
        logger.info("[TEST] 🔍 Verifying Homepage Layout")
        
        # 1. Verify Title
        expect(home_page.page).to_have_title(re.compile("Pinterest"))
        
        # 2. Verify Search Box (Dùng locator từ PO nếu public, hoặc định nghĩa logic check)
        # Tạm thời check URL để đảm bảo đang ở Home
        expect(home_page.page).to_have_url(re.compile(f"{settings.urls.base_ui}.*"))
        
        logger.info("[TEST] ✅ Homepage layout looks good")