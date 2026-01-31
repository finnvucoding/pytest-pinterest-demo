from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path

from config.settings import settings
from core.logger import get_logger

logger = get_logger()


class HTTPMethod(Enum):
    """Supported HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class APIResponse:
    """
    Structured API response wrapper.
    
    Lợi ích:
    - Type-safe: IDE autocomplete hoạt động
    - Test-friendly: Dễ assert với .is_ok, .data
    - Debug-friendly: error_message rõ ràng
    """
    status_code: int
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    success: bool = True
    error_message: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    
    @property
    def is_ok(self) -> bool:
        """Check if response is successful (2xx)."""
        return 200 <= self.status_code < 300
    
    @property
    def is_created(self) -> bool:
        """Check if resource was created (201)."""
        return self.status_code == 201
    
    @property
    def is_not_found(self) -> bool:
        """Check if resource not found (404)."""
        return self.status_code == 404


class BaseAPIClient:  
    MAX_RETRIES: int = 3
    BACKOFF_FACTOR: float = 0.5
    RETRY_STATUS_CODES: List[int] = [429, 500, 502, 503, 504]
    
    def __init__(self, base_url: str):
        """
        Initialize API Client.
        
        Args:
            base_url: API endpoint base URL
        """
        self._base_url = base_url.rstrip("/")  # Remove trailing slash
        self._session = self._create_session()
        logger.debug(f"🔌 API Client initialized. Endpoint: {self._base_url}")
    
    def _create_session(self) -> requests.Session:
        """
        Create requests Session with retry strategy.
        
        Retry giúp xử lý:
        - 429: Rate limited
        - 5xx: Server errors
        """
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.BACKOFF_FACTOR,
            status_forcelist=self.RETRY_STATUS_CODES,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update(settings.default_headers)
        
        return session
    
    # ==================== GENERIC HTTP METHODS ====================
    
    def get(
        self, 
        endpoint: str, 
        params: Optional[Dict] = None
    ) -> APIResponse:
        """HTTP GET request."""
        return self._make_request(HTTPMethod.GET, endpoint, params=params)
    
    def post(
        self, 
        endpoint: str, 
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> APIResponse:
        """HTTP POST request."""
        return self._make_request(HTTPMethod.POST, endpoint, data=data, json_data=json_data)
    
    def put(
        self, 
        endpoint: str, 
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> APIResponse:
        """HTTP PUT request."""
        return self._make_request(HTTPMethod.PUT, endpoint, data=data, json_data=json_data)
    
    def patch(
        self, 
        endpoint: str, 
        json_data: Optional[Dict] = None
    ) -> APIResponse:
        """HTTP PATCH request."""
        return self._make_request(HTTPMethod.PATCH, endpoint, json_data=json_data)
    
    def delete(self, endpoint: str) -> APIResponse:
        """HTTP DELETE request."""
        return self._make_request(HTTPMethod.DELETE, endpoint)
    
    # ==================== CORE REQUEST HANDLER ====================
    
    def _make_request(
        self,
        method: HTTPMethod,
        endpoint: str,
        data: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> APIResponse:
        """
        Centralized request handler.
        
        Mọi request đều đi qua đây để:
        - Logging tập trung
        - Error handling nhất quán
        - Response transformation
        """
        url = f"{self._base_url}{endpoint}"
        
        logger.debug(f"📡 [{method.value}] {url}")
        if json_data:
            logger.debug(f"   Payload: {json_data}")
        
        try:
            response = self._session.request(
                method=method.value,
                url=url,
                data=data,
                json=json_data,
                params=params,
                timeout=settings.timeouts.DEFAULT_TIMEOUT / 1000,  # ms → seconds
            )
            
            return self._process_response(response)
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️ [API] Timeout: {url}")
            return APIResponse(
                status_code=408,
                success=False,
                error_message="Request timed out"
            )
        except requests.exceptions.ConnectionError as e:
            logger.error(f"❌ [API] Connection Error: {str(e)}")
            return APIResponse(
                status_code=503,
                success=False,
                error_message=f"Connection failed: {str(e)}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ [API] Request Error: {str(e)}")
            return APIResponse(
                status_code=500,
                success=False,
                error_message=str(e)
            )
    
    def _process_response(self, response: requests.Response) -> APIResponse:
        """Convert requests.Response to our APIResponse wrapper."""
        try:
            data = response.json() if response.text else {}
        except ValueError:
            data = {"raw_text": response.text[:500]}  # Truncate for debugging
        
        log_level = "✅" if response.ok else "⚠️"
        logger.debug(f"   {log_level} Status: {response.status_code}")
        
        return APIResponse(
            status_code=response.status_code,
            data=data,
            success=response.ok,
            error_message="" if response.ok else response.reason,
            headers=dict(response.headers)
        )
    
    def close(self) -> None:
        """Close the session. Dùng khi teardown."""
        self._session.close()
        logger.debug("🔌 API Client session closed")
    
    # Context Manager support (Pythonic!)
    def __enter__(self) -> "BaseAPIClient":
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


class PinterestAPIClient(BaseAPIClient):
    """
    Pinterest-specific API Client.
    
    Kế thừa BaseAPIClient, thêm các business methods cho Pinterest.
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Pinterest API Client.
        
        Args:
            base_url: Override URL (useful for testing với mock server)
        """
        url = base_url or settings.urls.base_api
        super().__init__(url)
    
    # ==================== PINTEREST BUSINESS METHODS ====================
    
    def search_pins(self, keyword: str) -> APIResponse:
        """
        Search pins by keyword.
        
        Note: Pinterest không có public search API.
        Đây là mock method để demo structure.
        """
        logger.info(f"📡 [Pinterest] Searching: '{keyword}'")
        return self.get("/search/pins/", params={"q": keyword})
    
    def get_user_profile(self, username: str) -> APIResponse:
        """Get user profile by username."""
        return self.get(f"/users/{username}/")
    
    # ==================== FILE DOWNLOAD ====================
    
    def download_file(self, url: str, save_path: Path) -> bool:
        """
        Download file từ URL và lưu vào path.
        
        Dùng stream để không load toàn bộ vào memory (quan trọng với file lớn).
        """
        try:
            response = self._session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(save_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"⬇️ Downloaded: {save_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Download failed for {url}: {e}")
            return False


class JSONPlaceholderClient(BaseAPIClient):
    """
    JSONPlaceholder API Client.
    
    API thật để học và test: https://jsonplaceholder.typicode.com
    Có đầy đủ CRUD operations.
    """
    
    BASE_URL = "https://jsonplaceholder.typicode.com"
    
    def __init__(self):
        super().__init__(self.BASE_URL)
    
    # ==================== POSTS ENDPOINTS ====================
    
    def get_all_posts(self) -> APIResponse:
        """Get all posts (100 items)."""
        return self.get("/posts")
    
    def get_post(self, post_id: int) -> APIResponse:
        """Get single post by ID."""
        return self.get(f"/posts/{post_id}")
    
    def create_post(self, title: str, body: str, user_id: int = 1) -> APIResponse:
        """Create a new post."""
        return self.post("/posts", json_data={
            "title": title,
            "body": body,
            "userId": user_id
        })
    
    def update_post(self, post_id: int, title: str, body: str) -> APIResponse:
        """Update existing post (full update)."""
        return self.put(f"/posts/{post_id}", json_data={
            "id": post_id,
            "title": title,
            "body": body,
            "userId": 1
        })
    
    def patch_post(self, post_id: int, **fields) -> APIResponse:
        """Partial update post."""
        return self.patch(f"/posts/{post_id}", json_data=fields)
    
    def delete_post(self, post_id: int) -> APIResponse:
        """Delete a post."""
        return self.delete(f"/posts/{post_id}")
    
    # ==================== USERS ENDPOINTS ====================
    
    def get_all_users(self) -> APIResponse:
        """Get all users (10 items)."""
        return self.get("/users")
    
    def get_user(self, user_id: int) -> APIResponse:
        """Get single user by ID."""
        return self.get(f"/users/{user_id}")
    
    def get_user_posts(self, user_id: int) -> APIResponse:
        """Get all posts by a specific user."""
        return self.get(f"/users/{user_id}/posts")
    
    # ==================== COMMENTS ENDPOINTS ====================
    
    def get_post_comments(self, post_id: int) -> APIResponse:
        """Get comments for a specific post."""
        return self.get(f"/posts/{post_id}/comments")