import logging
import sys
from config.settings import settings

class LogConfig:
    _logger = None

    @classmethod
    def get_logger(cls, name: str = "PinterestAuto") -> logging.Logger:
        if cls._logger:
            return cls._logger

        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)

        # Nếu logger đã có handler (do thư viện khác hoặc lần gọi trước), không add thêm
        if logger.hasHandlers():
            cls._logger = logger
            return logger

        # --- FORMATTER ---
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # --- 1. CONSOLE HANDLER (Stream) ---
        # Dùng stderr để tách biệt với output chương trình
        c_handler = logging.StreamHandler(sys.stderr)
        c_handler.setLevel(logging.INFO)
        c_handler.setFormatter(formatter)
        logger.addHandler(c_handler)

        # --- 2. FILE HANDLER (Rotating/Unique) ---
        log_dir = settings.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        # Tên file chứa cả Giờ-Phút-Giây để tách biệt từng lần chạy (Run Isolation)
        log_file = log_dir / f"run_{settings.get_current_timestamp()}.log"

        f_handler = logging.FileHandler(log_file, encoding="utf-8")
        f_handler.setLevel(logging.DEBUG)
        f_handler.setFormatter(formatter)
        logger.addHandler(f_handler)

        # Lưu lại instance
        cls._logger = logger
        
        logger.info(f"🚀 Logger initialized. Writing to: {log_file}")
        return logger

# Helper function để import gọn: from core.logger import log
def log() -> logging.Logger:
    return LogConfig.get_logger()

# Alias for get_logger: from core.logger import get_logger
def get_logger(name: str = "PinterestAuto") -> logging.Logger:
    return LogConfig.get_logger(name)