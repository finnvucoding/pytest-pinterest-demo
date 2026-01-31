import pytest
from pathlib import Path
from typing import Generator
from playwright.sync_api import Page

from config.settings import settings
from core.logger import get_logger
from utils.pinterest_api import PinterestAPIClient

from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.search_result_page import SearchResultPage

logger = get_logger()

# ==================== HOOKS (REPORTING) ====================

def pytest_configure(config):
    """Start-up Hook"""
    logger.info(f"🚀 TEST SESSION STARTING | Env: {settings.environment.value}")
    
    markers = ["smoke", "regression", "slow"]
    for marker in markers:
        config.addinivalue_line("markers", f"{marker}: {marker} tests")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test result for screenshot/video logic"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

# ==================== CORE FIXTURES ====================

@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    """
    Nếu HEADLESS=false trong .env → browser sẽ hiện lên (headed mode)
    """
    return {
        **browser_type_launch_args,
        "headless": settings.browser.HEADLESS,  # Đọc từ .env
        "slow_mo": settings.browser.SLOW_MO,    # Bonus: thêm slow_mo từ env
    }

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Global Context Configuration.
    Override fixture mặc định của pytest-playwright.
    """
    # 1. Video Configuration
    video_dir = None
    if settings.browser.RECORD_VIDEO:
        video_path = settings.project_root / "logs" / "videos"
        video_path.mkdir(parents=True, exist_ok=True)
        video_dir = str(video_path) # Playwright yêu cầu path string

    # 2. Context Options
    return {
        **browser_context_args,
        "viewport": settings.browser.VIEWPORT,
        "locale": settings.browser.LOCALE,
        "ignore_https_errors": True,
        "record_video_dir": video_dir,
        "record_video_size": settings.browser.VIEWPORT,
        # Thêm permissions nếu cần (ví dụ cho paste clipboard)
        # "permissions": ["clipboard-read", "clipboard-write"],
    }

# ==================== ARTIFACTS FIXTURES (UI ONLY) ====================

def _is_ui_test(request) -> bool:
    """
    Check if current test is a UI test (needs browser).
    
    Logic: Nếu test nằm trong tests/ui/ hoặc request page fixture → UI test.
    API tests trong tests/api/ sẽ không được áp dụng auto_artifacts_handler.
    """
    # Check if test file is in api/ folder
    test_file = str(request.fspath)
    return "tests\\api" not in test_file and "tests/api" not in test_file


@pytest.fixture(scope="function", autouse=True)
def auto_artifacts_handler(request):
    """
    Combined fixture xử lý cả Screenshot và Video Rename.
    
    CHỈ apply cho UI tests - skip cho API tests.
    """
    # Skip cho API tests (không có browser)
    if not _is_ui_test(request):
        yield
        return
    
    # UI tests cần page fixture
    page = request.getfixturevalue("page")
    
    yield  # Chờ test chạy xong

    # 1. Lấy kết quả test an toàn
    rep_call = getattr(request.node, "rep_call", None)
    rep_setup = getattr(request.node, "rep_setup", None)
    
    # Check if failed (either in setup or call)
    failed = (rep_call and rep_call.failed) or (rep_setup and rep_setup.failed)
    
    # Tạo tên file an toàn
    test_name = request.node.name
    safe_name = test_name.replace(" ", "_").replace("[", "_").replace("]", "_")
    timestamp = settings.get_current_timestamp() # Giả sử settings có hàm này
    
    # --- HANDLING SCREENSHOT ---
    if failed:
        screenshot_path = settings.project_root / "screenshots" / f"FAIL_{safe_name}_{timestamp}.png"
        screenshot_path.parent.mkdir(exist_ok=True)
        try:
            page.screenshot(path=str(screenshot_path), full_page=True)
            logger.error(f"📸 Screenshot saved: {screenshot_path.name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to take screenshot: {e}")

    # --- HANDLING VIDEO ---
    if settings.browser.RECORD_VIDEO:
        try:
            # Đóng page để đảm bảo video file được finalize (flush xuống đĩa)
            page.close()
            
            video = page.video
            if video:
                original_path = Path(video.path())
                status_prefix = "FAIL" if failed else "PASS"
                new_name = f"{status_prefix}_{safe_name}_{timestamp}.webm"
                new_path = original_path.parent / new_name
                
                # Rename an toàn
                video.save_as(str(new_path))
                
                # Delete gốc (với retry nhẹ để tránh lỗi file locked trên Windows)
                if original_path.exists() and original_path != new_path:
                    try:
                        original_path.unlink()
                    except PermissionError:
                        logger.warning(f"⚠️ File locked, could not delete original video: {original_path.name}")
                
                logger.info(f"📹 Video saved: {new_name}")
        except Exception as e:
            logger.warning(f"⚠️ Video rename failed: {e}")

# ==================== PAGE OBJECT FIXTURES ====================

@pytest.fixture(scope="function")
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)

@pytest.fixture(scope="function")
def home_page(page: Page) -> HomePage:
    return HomePage(page)

@pytest.fixture(scope="function")
def search_result_page(page: Page) -> SearchResultPage:
    return SearchResultPage(page)

# ==================== API FIXTURE ====================

@pytest.fixture(scope="session")
def api_client() -> Generator[PinterestAPIClient, None, None]:
    client = PinterestAPIClient()
    yield client
    client.close()