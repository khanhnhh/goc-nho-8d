# Khởi động nhanh

## Cài đặt (1 lần)

```bash
cd nguoi-ban-nho-ai
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Chạy server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Mở: http://localhost:8000

## Chạy test

```bash
pip install pytest pytest-asyncio
pytest tests/test_redteam.py -v
```
