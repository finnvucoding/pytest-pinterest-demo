# Pinterest Test Automation 🎯

Automation testing framework cho Pinterest sử dụng **Playwright** + **Pytest**.

## 📁 Cấu trúc

```
Pinterest_test/
├── config/         # Cấu hình (settings, environment)
├── core/           # Base page, logger
├── pages/          # Page Object Models
├── tests/ui/       # Test cases
├── utils/          # API client, helpers
├── downloads/      # Ảnh tải về
├── screenshots/    # Screenshot khi test fail
└── reports/        # HTML reports
```

## ⚡ Cài đặt

```bash
# 1. Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 2. Cài dependencies
pip install -r requirements.txt

# 3. Cài Playwright browsers
playwright install chromium
```

## 🔐 Cấu hình

Tạo file `.env`:

```env
PINTEREST_EMAIL=your_email@gmail.com
PINTEREST_PASSWORD=your_password
HEADLESS=false
SLOW_MO=0
RECORD_VIDEO=true
```

## 🚀 Chạy Test

```bash
# Chạy tất cả tests
pytest

# Chạy với browser hiển thị
pytest --headed

# Chạy test cụ thể
pytest tests/ui/test_pinterest_search.py
pytest tests/ui/test_download_5_img.py

# Chạy theo marker
pytest -m smoke

# Chạy với HTML report
pytest --html=reports/report.html
```

## 📋 Markers

| Marker | Mô tả |
|--------|-------|
| `smoke` | Quick sanity tests |
| `regression` | Full regression |
| `slow` | Slow tests |
| `api` | API tests |

## 🛠 Tech Stack

- Python 3.10+
- Playwright
- Pytest
- pytest-html (reports)
