# Góc nhỏ 8D — Chatbot hỗ trợ tâm lý ẩn danh

> Demo kỹ thuật cho sáng kiến CN03 — "Thiết kế Chatbot AI nhằm tăng cường hỗ trợ tâm lý và điều chỉnh hành vi cho học sinh lớp 8" của cô Nguyễn Thị Mỹ Dung, THCS Hưng Chính.

## Tính năng

✅ **Ẩn danh hoàn toàn** — không đăng nhập, không thu thập PII  
✅ **4 lớp phòng thủ** — rate limit, crisis detection, PII masking, output validation  
✅ **Cảnh báo khủng hoảng** — template cố định + thông báo GVCN khi phát hiện từ khóa nguy hiểm  
✅ **Dashboard GVCN** — báo cáo tuần ẩn danh  
✅ **Mobile-first** — web chat responsive, có thể cài làm PWA  
✅ **Red-team tests** — 50+ kịch bản đối kháng  

## Cài đặt

```bash
# 1. Tạo virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# hoặc
.venv\Scripts\activate     # Windows

# 2. Cài đặt dependencies
pip install -r requirements.txt

# 3. Cấu hình
cp .env.example .env
# Chỉnh LLM_PROVIDER=mock (hoặc openai/anthropic) và điền API key

# 4. Chạy server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Mở trình duyệt: http://localhost:8000

## Cấu trúc dự án

```
goc-nho-8d/
├── backend/
│   ├── main.py                 # FastAPI — điều phối 4 lớp phòng thủ
│   ├── config.py               # Đọc .env, load prompts và từ khóa
│   ├── prompts/
│   │   ├── system.md           # System prompt (persona + luật)
│   │   └── few_shots.json      # Hội thoại mẫu do GVCN duyệt
│   ├── guardrails/
│   │   ├── input_filter.py     # Lớp 1: crisis detection, PII masking, rate limit
│   │   ├── output_validator.py # Lớp 3: blacklist, cấu trúc
│   │   └── crisis.py           # Lớp 4: template khủng hoảng
│   ├── llm/
│   │   ├── base.py             # Abstract base class
│   │   ├── mock.py             # Mock LLM cho test
│   │   ├── openai_client.py    # OpenAI GPT-4o-mini
│   │   └── anthropic_client.py # Claude Haiku
│   ├── storage/
│   │   └── sessions.py         # SQLite ẩn danh, TTL 30 ngày
│   └── notify/
│       └── teacher.py          # Gửi cảnh báo GVCN (email/Zalo)
├── frontend/
│   ├── index.html              # Web chat mobile-first
│   ├── dashboard.html          # Dashboard GVCN
│   ├── css/
│   │   ├── style.css
│   │   └── dashboard.css
│   ├── js/
│   │   ├── chat.js
│   │   └── dashboard.js
│   └── manifest.json           # PWA manifest
├── config/
│   ├── crisis_keywords.txt     # Từ khóa khủng hoảng (GVCN + kỹ sư duyệt)
│   └── blacklist.txt           # Từ cấm trong câu trả lời
├── tests/
│   └── test_redteam.py         # 50+ kịch bản đối kháng
├── requirements.txt
└── README.md
```

## Chạy test

```bash
# Cài pytest
pip install pytest pytest-asyncio

# Chạy red-team tests
pytest tests/test_redteam.py -v
```

## Chuyển sang LLM thật

Mở `.env`, đổi:

```env
LLM_PROVIDER=openai  # hoặc anthropic
OPENAI_API_KEY=sk-your-key-here
```

Khởi động lại server.

## Triển khai sản xuất

1. **Hosting**: Render, Fly.io, hoặc VPS (~200k VND/tháng)
2. **LLM API**: OpenAI GPT-4o-mini (~100-300k VND/tháng cho 40 học sinh)
3. **Thông báo GVCN**: tích hợp email SMTP hoặc webhook Zalo thật
4. **HTTPS**: bắt buộc (Let's Encrypt miễn phí)
5. **Backup DB**: tự động hàng ngày

## Pháp lý & đạo đức

✅ Không thu thập PII, TTL 30 ngày  
✅ Che PII bằng regex trước khi gọi LLM  
✅ API nước ngoài (OpenAI/Anthropic) — dữ liệu đã ẩn danh  
⚠️ Nếu cần tuyệt đối tuân thủ Nghị định 13/2023/NĐ-CP: dùng API trong nước (Zalo AI, FPT AI) hoặc tự host mô hình mở  

## Phát triển thêm

- [ ] Tích hợp LLM-as-judge (lớp 3 nâng cao)
- [ ] Dashboard chi tiết hơn (biểu đồ xu hướng cảm xúc)
- [ ] Export báo cáo PDF cho GVCN
- [ ] Đa ngôn ngữ (tiếng Anh cho học sinh quốc tế)
- [ ] Tích hợp chuyên gia tâm lý học đường (chat tay)

## Liên hệ

**Sáng kiến**: Nguyễn Thị Mỹ Dung — THCS Hưng Chính  
**Kỹ thuật**: kho (software engineer)

## Giấy phép

Demo kỹ thuật cho mục đích giáo dục. Vui lòng ghi nguồn khi sử dụng.
