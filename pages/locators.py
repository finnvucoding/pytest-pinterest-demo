from dataclasses import dataclass

@dataclass(frozen=True)
class HomePageLocators:
    # 1. Technical Selectors (CSS/ID - Dùng page.locator) - ƯU TIÊN 1
    SEARCH_INPUT_SELECTOR: str = "[data-test-id='search-box-input']"
    NAV_HOME_BTN: str = "[data-test-id='pinterest-logo-home-button']"
    
    # 2. Fallback: Dùng name attribute (bền vững hơn placeholder)
    SEARCH_INPUT_BY_NAME: str = "input[name='searchBoxInput']"
    
    # 3. User-Facing Labels (Text - Phụ thuộc ngôn ngữ, chỉ dùng làm fallback cuối)
    # Regex pattern để match nhiều ngôn ngữ: "Search", "Tìm kiếm", "検索", etc.
    SEARCH_PLACEHOLDER_PATTERN: str = r"Search|Tìm kiếm|搜索|検索|Rechercher"

@dataclass(frozen=True)
class LoginPageLocators:
    # Google One Tap popup - dùng selector cụ thể hơn
    GOOGLE_POPUP_CONTAINER: str = "#credentials-picker-container"
    GOOGLE_POPUP_CLOSE_BTN: str = "#credentials-picker-container #close"

    LOGIN_BTN_LABEL: str = "[data-test-id='simple-login-button']" 

    EMAIL_INPUT: str = "[data-test-id='emailInputField']"
    PASSWORD_INPUT: str = "[data-test-id='passwordInputField']"
    SUBMIT_BTN: str = "[data-test-id='registerFormSubmitButton']"
    
@dataclass(frozen=True)
class SearchResultPageLocators:
    # Container chứa tất cả pins
    FEED_GRID: str = "[data-test-id='max-width-container']"
    
    # Mỗi item trong grid (dùng để đếm số lượng pins)
    GRID_ITEM: str = "[data-grid-item='true']"
    
    # Pin card (bên trong mỗi grid item)
    PIN_ITEM: str = "[data-test-id='pin']"
    PIN_WRAPPER: str = "[data-test-id='pinWrapper']"
    
    # Hình ảnh đã load xong (có src từ pinimg.com)
    PIN_IMAGE_LOADED: str = "[data-test-id='non-story-pin-image'] img[src*='pinimg.com']"
    
    # Footer chứa title của pin
    PIN_TITLE: str = "[data-test-id='pinrep-footer-organic-title']"