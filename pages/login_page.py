from config.settings import settings
from core.base_page import BasePage
from core.logger import get_logger
from pages.locators import LoginPageLocators as Loc

logger = get_logger()

class LoginPage(BasePage):
    """
    Page Object cho Pinterest Login Page.
    Kế thừa BasePage mới (Thin Wrapper).
    """
    def navigate(self):
        """Mở trang Login"""
        login_url = f"{settings.urls.base_ui}/login/"
        self.open(login_url)
        self.page.wait_for_timeout(settings.timeouts.SHORT24_TIMEOUT)

        # if "pinterest.com" not in self.page.url:
        #     self.open(settings.urls.base_ui)
        
        # # Click nút Login
        # login_btn = self.page.locator(Loc.LOGIN_BTN_LABEL)
        # self.click(login_btn, description="Login Button")
        
        # # Chờ form login xuất hiện
        # self.page.locator(Loc.EMAIL_INPUT).wait_for(state="visible", timeout=5000)
        # logger.info("📝 Login form opened")
    
    def _dismiss_google_popup(self):
        """
        Tắt popup 'Đăng nhập bằng Google' (Google One Tap) nếu xuất hiện.
        Popup này gây trở ngại khi click vào ô email trên Firefox.
        """
        try:
            google_popup = self.page.locator(Loc.GOOGLE_POPUP_CONTAINER)
            
            # Đợi tối đa 2 giây xem popup có xuất hiện không
            if google_popup.is_visible(timeout=2000):
                logger.info("🔔 Google One Tap popup detected, dismissing...")
                
                close_btn = self.page.locator(Loc.GOOGLE_POPUP_CLOSE_BTN)
                close_btn.wait_for(state="visible", timeout=2000)
                close_btn.click()
                
                # Đợi popup biến mất
                google_popup.wait_for(state="hidden", timeout=3000)
                logger.info("✅ Google popup dismissed")
                
        except Exception as e:
            # Popup không xuất hiện hoặc đã tự tắt - thử nhấn Escape
            logger.debug(f"Google popup handling: {e}")
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
    
    def login(self, email: str, password: str):
        # Đóng popup Google nếu có
        self._dismiss_google_popup()
        
        logger.info(f"🔑 Logging in as: {email}")

        email_input = self.page.locator(Loc.EMAIL_INPUT)
        logger.info("⌨️ Typing email into 'Email Input'")
        email_input.click()
        self.page.wait_for_timeout(settings.timeouts.TYPING_TIMEOUT)
        email_input.type(email, delay=settings.timeouts.TYPING_TIMEOUT)  # Gõ từng ký tự chậm
        
        self.page.wait_for_timeout(settings.timeouts.SHORT13_TIMEOUT)
        
        password_input = self.page.locator(Loc.PASSWORD_INPUT)
        logger.info("⌨️ Typing password into 'Password Input'")
        password_input.click()
        self.page.wait_for_timeout(settings.timeouts.TYPING_TIMEOUT)
        password_input.type(password, delay=settings.timeouts.TYPING_TIMEOUT)  # Gõ từng ký tự chậm

        self.page.wait_for_timeout(settings.timeouts.SHORT13_TIMEOUT)
        
        # 2. Click Submit
        self.click(
            self.page.locator(Loc.SUBMIT_BTN), 
            description="Login Button"
        )

        # 3. Wait for Success (Quan trọng)
        self.wait_for_url_change()
    
    # --- CHECKS / VERIFICATIONS ---

    def wait_for_url_change(self):
        """Chờ URL thoát khỏi trang login"""
        try:
            # Chờ URL không chứa 'login' nữa
            self.page.wait_for_url(lambda url: "/login" not in url, timeout=15000)
            logger.info("✅ Login redirect successful")
            self.page.wait_for_timeout(settings.timeouts.SHORT24_TIMEOUT)
        except Exception:
            logger.warning("⚠️ Login timeout or failed to redirect")

    def get_error_message(self) -> str:
        """Lấy text lỗi nếu login sai"""
        # Giả sử trong locators.py có ERROR_MSG
        error_loc = self.page.locator("[data-test-id='login-error']") 
        
        if self.is_visible_slow(error_loc):
            return self.get_text(error_loc, description="Error Message")
        return ""