from typing import List

from config.settings import settings
from core.base_page import BasePage
from core.logger import get_logger
from pages.locators import SearchResultPageLocators as Loc

logger = get_logger()

class SearchResultPage(BasePage):
    """
    Page Object for Pinterest Search Results.
    Refactored to match new BasePage architecture.
    """

    # --- ACTIONS ---

    def click_pin(self, index: int = 0):
        """Click on a specific pin by index"""
        logger.info(f"🖱️ Clicking pin at index {index}")
        
        # Get all pins
        pins = self.page.locator(Loc.PIN_ITEM)
        
        # Ensure we have enough pins
        if pins.count() <= index:
            raise Exception(f"Cannot click pin #{index}, only found {pins.count()} pins.")
            
        # Click the Nth pin
        target_pin = pins.nth(index)
        self.click(target_pin, description=f"Pin #{index}")

    def load_more_by_scrolling(self, scrolls: int = 3):
        """Scroll down to trigger infinite load"""
        logger.info(f"📜 Scrolling {scrolls} times to load more pins...")
        for _ in range(scrolls):
            self.page.mouse.wheel(0, 5000) # Scroll down 5000px
            self.page.wait_for_timeout(settings.timeouts.SHORT13_TIMEOUT) # Wait for network/render

    def get_image_urls(self, limit: int = 5) -> List[str]:
        logger.info(f"🔍 Extracting top {limit} image URLs...")
        
        self.wait_for_results(min_count=limit)
        
        images = self.page.locator(Loc.PIN_IMAGE_LOADED)
        
        urls = []
        # Lấy số lượng thực tế (có thể ít hơn limit nếu hết kết quả)
        count = min(images.count(), limit)
        
        logger.debug(f"📷 Found {images.count()} loaded images, extracting {count}")
        
        for i in range(count):
            img = images.nth(i)
            
            srcset = img.get_attribute("srcset")
            src = img.get_attribute("src")
            
            final_url = ""
            
            if srcset:
                # Format: "url_1x 1x, url_2x 2x, url_4x 4x"
                # Get the highest resolution (last one)
                try:
                    final_url = srcset.split(",")[-1].strip().split(" ")[0]
                except IndexError:
                    final_url = src # Fallback if parsing fails
            elif src:
                final_url = src
                
            if final_url:
                urls.append(final_url)
                logger.debug(f"✅ Image {i+1}: {final_url}")
                
        logger.info(f"📝 Extracted {len(urls)} URLs")
        return urls
    
    # --- CHECKS / DATA RETRIEVAL ---

    def get_loaded_pins_count(self) -> int:
        """Return total number of visible pins"""
        count = self.page.locator(Loc.PIN_ITEM).count()
        logger.debug(f"👀 Found {count} pins on screen")
        return count

    def wait_for_results(self, min_count: int = 1, timeout: int = 10000) -> int:
        """
        Wait until at least N pins are visible.
        Returns the actual count found.
        """
        logger.info(f"⏳ Waiting for at least {min_count} pins to load...")
        
        try:
            # Smart Wait: Wait for the Nth element to be attached to DOM
            # nth(min_count - 1) means if we want 5 items, we wait for index 4 to exist
            self.page.locator(Loc.PIN_ITEM).nth(min_count - 1).wait_for(state="visible", timeout=timeout)
        except Exception:
            logger.warning(f"⚠️ Timeout waiting for {min_count} pins.")
        
        return self.get_loaded_pins_count()

    def get_all_pin_titles(self) -> List[str]:
        """Get text description/titles of visible pins"""
        # Dùng PIN_TITLE locator để lấy tiêu đề chính xác
        return self.page.locator(Loc.PIN_TITLE).all_inner_texts()

    def is_no_results(self) -> bool:
        """
        Check if search returned no results.
        Logic: Nếu FEED_GRID không xuất hiện → không có kết quả.
        """
        has_grid = self.is_visible_slow(self.page.locator(Loc.FEED_GRID), timeout=5000)
        if not has_grid:
            logger.info("🚫 No search results - FEED_GRID not found")
        return not has_grid