import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
import random

load_dotenv()

class Environment(Enum):
    """Supported test environments."""
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"

# Định nghĩa Map URL cho từng môi trường
ENV_URLS = {
    Environment.LOCAL: "http://localhost:3000",
    Environment.STAGING: "https://staging.pinterest.com", # Assumed staging URL
    Environment.PRODUCTION: "https://www.pinterest.com"
}

ENV_API_URLS = {
    Environment.LOCAL: "http://localhost:8000/v3",
    Environment.STAGING: "https://api-staging.pinterest.com/v3",
    Environment.PRODUCTION: "https://api.pinterest.com/v3"
}


@dataclass(frozen=True)
class URLConfig:
    """URL configurations generated based on Environment."""
    base_ui: str
    base_api: str
    login_path: str = "/login/"

    @property
    def full_login_url(self) -> str:
        return f"{self.base_ui}{self.login_path}"


@dataclass(frozen=True)
class TimeoutConfig:
    """Timeout configurations in milliseconds."""
    DEFAULT_TIMEOUT: int = 30000
    TYPING_TIMEOUT: int = random.randint(300, 500)
    SHORT13_TIMEOUT: int = random.randint(1000, 3000)
    SHORT24_TIMEOUT: int = random.randint(2000, 4000)
    LONG_TIMEOUT: int = 60000
    PAGE_LOAD_TIMEOUT: int = 45000
    ELEMENT_TIMEOUT: int = 10000


@dataclass(frozen=True)
class BrowserSettings:
    """Browser configurations."""
    HEADLESS: bool = field(
        default_factory=lambda: os.getenv("HEADLESS", "false").lower() == "true"
    )
    # Slow mo nên lấy từ env để debug dễ hơn
    SLOW_MO: int = field(
        default_factory=lambda: int(os.getenv("SLOW_MO", "0"))
    )
    VIEWPORT: Dict[str, int] = field(
        default_factory=lambda: {"width": 1080, "height": 720}
    )
    LOCALE: str = "en-US"

    RECORD_VIDEO: bool = field(
        default_factory=lambda: os.getenv("RECORD_VIDEO", "false").lower() == "true"
    )

@dataclass(frozen=True)
class TestCredentials:
    """Test account credentials."""
    email: str = field(default_factory=lambda: os.getenv("PINTEREST_EMAIL", ""))
    password: str = field(default_factory=lambda: os.getenv("PINTEREST_PASSWORD", ""))
    
    @property
    def is_valid(self) -> bool:
        return bool(self.email and self.password)


class Settings:
    def __init__(self):
        self.environment = self._get_environment()
        self.project_root = Path(__file__).parent.parent
        
        # Init configs
        self.urls = self._configure_urls()
        self.timeouts = TimeoutConfig()
        self.browser = BrowserSettings()
        self.credentials = TestCredentials()

    def _get_environment(self) -> Environment:
        env_str = os.getenv("TEST_ENV", "production").lower()
        try:
            return Environment(env_str)
        except ValueError:
            print(f"[WARNING] Unknown env '{env_str}', falling back to PRODUCTION")
            return Environment.PRODUCTION

    def _configure_urls(self) -> URLConfig:
        """Chọn URL dựa trên Environment"""
        return URLConfig(
            base_ui=ENV_URLS.get(self.environment, ENV_URLS[Environment.PRODUCTION]),
            base_api=ENV_API_URLS.get(self.environment, ENV_API_URLS[Environment.PRODUCTION])
        )
    
    @property
    def default_headers(self) -> Dict[str, str]:
        """Default HTTP headers for API requests."""
        return {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/135.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9"
        }

    def get_current_timestamp(self) -> str:
        """Get current timestamp for filenames."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


settings = Settings()
