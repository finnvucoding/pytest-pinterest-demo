import pytest
from config.settings import settings
from core.logger import get_logger
from utils.pinterest_api import PinterestAPIClient

# Page Objects
from pages.home_page import HomePage
from pages.search_result_page import SearchResultPage
from pages.login_page import LoginPage

logger = get_logger()

DOWNLOAD_DIR = settings.project_root / "downloads"

@pytest.mark.smoke
class TestImageDownload:
    
    @pytest.fixture(scope="function", autouse=True)
    def setup_auth(self, login_page: LoginPage):
        """Đảm bảo đã login (Dùng lại fixture đã học)"""
        login_page.navigate()
        login_page.login(settings.credentials.email, settings.credentials.password)

    def test_download_high_res_images(
        self,
        home_page: HomePage,
        search_result_page: SearchResultPage,
        api_client: PinterestAPIClient # Dùng để download
    ):
        # --- 1. SEARCH ---
        keyword = "4K Wallpaper"
        home_page.search_for(keyword)
        
        # --- 2. GET URLS ---
        # Logic phức tạp đã ẩn trong Page Object
        target_count = 5
        image_urls = search_result_page.get_image_urls(limit=target_count)
        
        assert len(image_urls) >= target_count, "Not enough images found"
        
        # --- 3. DOWNLOAD ---
        # Tạo folder riêng cho test này
        save_dir = DOWNLOAD_DIR / keyword.replace(" ", "_")
        save_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded_count = 0
        
        for i, url in enumerate(image_urls):
            # Tự động detect extension đơn giản (hoặc mặc định jpg)
            ext = ".jpg" if ".png" in url else ".png" if ".webp" in url else ".webp"
            
            file_name = f"img_{i+1}_{settings.get_current_timestamp()}{ext}"
            save_path = save_dir / file_name
            
            # Gọi Utils để download
            if api_client.download_file(url, save_path):
                downloaded_count += 1
                
        # --- 4. VERIFY ---
        assert downloaded_count == target_count, \
            f"Expected {target_count} downloads, got {downloaded_count}"
        
        # Check file size (sanity check)
        for file in save_dir.glob("*"):
            assert file.stat().st_size > 1024, f"File too small (broken?): {file.name}"
            
        logger.info(f"[TEST] ✅ Download test passed. Files at: {save_dir}")