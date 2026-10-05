# DocMind

Hệ thống hỏi đáp tài liệu cục bộ (Local Document Q&A), tương tự NotebookLM, chạy **100% offline** với Ollama và RAG pipeline. Hỗ trợ upload PDF, DOCX, TXT — tạo kịch bản system prompt tuỳ chỉnh — chat realtime với streaming.

---

## Tính năng

- **Upload đa định dạng** — PDF, DOCX, TXT; parse và embed tự động nền
- **RAG Pipeline** — truy xuất ngữ nghĩa qua ChromaDB, ghép context vào prompt
- **Kịch bản (Scenario)** — system prompt tuỳ chỉnh theo vai trò/mục đích, hỗ trợ biến Jinja2
- **Streaming realtime** — trả lời token-by-token qua SSE
- **Quản lý phiên** — nhiều session, mỗi session chọn riêng tài liệu + kịch bản
- **Chạy hoàn toàn offline** — không gửi dữ liệu ra ngoài

---

## System Design

### Kiến trúc tổng thể

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client (Browser)                         │
│                    HTML + CSS + Vanilla JS                      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼────────────────────────────────────┐
│                     FastAPI Web Server                          │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│   │ /docs    │  │ /sessions│  │ /chat    │  │ /health      │  │
│   │ /scenarios│  │          │  │  (SSE)   │  │              │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────────┘  │
│                                                                  │
│   ┌───────────────┐   ┌────────────────┐   ┌────────────────┐  │
│   │ DocumentSvc   │   │  RAG Service   │   │  LLM Client    │  │
│   │ parse→chunk   │   │ embed→retrieve │   │  (OpenAI API)  │  │
│   │ →embed→store  │   │                │   │                │  │
│   └──────┬────────┘   └───────┬────────┘   └───────┬────────┘  │
└──────────┼────────────────────┼────────────────────┼───────────┘
           │                    │                    │
    ┌──────▼──────┐    ┌────────▼────────┐   ┌──────▼──────┐
    │   SQLite    │    │    ChromaDB     │   │   Ollama    │
    │  (metadata) │    │  (vector store) │   │ gemma4:e4b  │
    └─────────────┘    └─────────────────┘   └─────────────┘
```

### RAG Pipeline

```
[Upload file]
      │
      ▼
[Parse] ──── PDF → PyMuPDF
         ├── DOCX → python-docx
         └── TXT  → plain read
      │
      ▼
[Chunk] ── RecursiveCharacterTextSplitter
           size=1500, overlap=200
      │
      ▼
[Embed] ── sentence-transformers/all-MiniLM-L6-v2
           (chạy local, Apple MPS / CPU)
      │
      ▼
[Store] ── ChromaDB (persistent, local disk)
           metadata: {document_id, source, page}

─────────────────────── Query time ───────────────────────

[User question]
      │
      ▼
[Embed question] ── all-MiniLM-L6-v2
      │
      ▼
[Retrieve top-K] ── ChromaDB similarity search
                    filter: document_id ∈ session.documents
      │
      ▼
[Build prompt] ── system prompt (Jinja2 rendered)
               ── context blocks (retrieved chunks)
               ── chat history
               ── user question
      │
      ▼
[Ollama stream] ── OpenAI-compatible API (localhost:11434/v1)
      │
      ▼
[SSE → Browser] ── token-by-token streaming
```

### Tech Stack

| Layer | Công nghệ |
|---|---|
| Web framework | FastAPI 0.109+ |
| ASGI server | Uvicorn |
| Template engine | Jinja2 |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite |
| Vector store | ChromaDB |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| LLM runtime | Ollama (OpenAI-compatible API) |
| LLM model | gemma4:e4b |
| PDF parser | PyMuPDF (fitz) |
| DOCX parser | python-docx |
| Text splitter | langchain-text-splitters |
| HTTP client | httpx, openai SDK |

---

## Software Design

### Cấu trúc thư mục

```
docmind/
├── run.py                      # Entry point
├── requirements.txt
├── .env                        # Cấu hình (không commit)
├── .env.example                # Template cấu hình
│
├── app/
│   ├── config.py               # Settings từ .env (pydantic-settings)
│   ├── database.py             # SQLAlchemy engine + session
│   ├── main.py                 # FastAPI app, routers, startup
│   ├── llm_client.py           # Ollama streaming client
│   ├── vector_store.py         # ChromaDB wrapper
│   ├── prompt_builder.py       # Ghép system prompt + context + history
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── document.py         # Document (file upload)
│   │   ├── scenario.py         # Scenario (system prompt template)
│   │   ├── session.py          # ChatSession + N-N session_documents
│   │   └── message.py          # Message (chat history)
│   │
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── document.py
│   │   ├── scenario.py
│   │   ├── session.py
│   │   └── message.py
│   │
│   ├── api/                    # FastAPI routers
│   │   ├── documents.py        # Upload, list, delete
│   │   ├── scenarios.py        # CRUD kịch bản
│   │   ├── sessions.py         # Tạo/xoá phiên chat
│   │   ├── chat.py             # Gửi message + SSE streaming
│   │   └── health.py           # Health check
│   │
│   ├── services/
│   │   ├── document_service.py # Background: parse → chunk → embed → store
│   │   ├── embedding_service.py# Load + cache embedding model
│   │   └── rag_service.py      # Retrieve + rank chunks
│   │
│   ├── parsers/
│   │   ├── base.py             # Abstract parser
│   │   ├── pdf_parser.py       # PyMuPDF
│   │   ├── docx_parser.py      # python-docx
│   │   └── text_parser.py      # Plain text
│   │
│   ├── templates/              # Jinja2 HTML templates
│   │   ├── base.html
│   │   ├── index.html          # Chat UI
│   │   ├── documents.html
│   │   └── scenarios.html
│   │
│   └── static/
│       ├── app.js              # Vanilla JS (SSE, fetch)
│       └── style.css
│
└── storage/                    # Dữ liệu runtime (không commit)
    ├── uploads/                # File gốc người dùng upload
    ├── chroma/                 # ChromaDB persistent data
    └── docmind.db              # SQLite database
```

### Luồng xử lý chính

**Upload tài liệu:**
```
POST /api/v1/documents/upload
  → lưu file vào storage/uploads/
  → tạo record Document (status=processing)
  → BackgroundTask: parse → chunk → embed → ChromaDB
  → cập nhật Document (status=ready)
```

**Chat:**
```
POST /api/v1/chat/{session_id}/messages
  → lấy session + documents + scenario
  → RAG: embed câu hỏi → top-K chunks từ ChromaDB
  → build prompt: system + context + history + question
  → stream từ Ollama qua SSE
  → lưu message vào DB
```

---

## Database Design

### ERD

```
┌─────────────────┐        ┌──────────────────────┐
│    Document     │        │   session_documents   │
├─────────────────┤        │  (N-N junction table) │
│ id (PK, UUID)   │◄───────│ session_id (FK)       │
│ filename        │        │ document_id (FK)      │
│ original_name   │        └──────────┬───────────┘
│ file_type       │                   │
│ file_size       │        ┌──────────▼───────────┐
│ status          │        │     ChatSession       │
│ chunk_count     │        ├──────────────────────┤
│ created_at      │        │ id (PK, UUID)         │
└─────────────────┘        │ title                 │
                           │ scenario_id (FK)      │◄──┐
                           │ temperature           │   │
                           │ created_at            │   │
                           └──────────┬────────────┘   │
                                      │                 │
                           ┌──────────▼────────────┐   │
                           │       Message         │   │
                           ├──────────────────────┤   │
                           │ id (PK, UUID)         │   │
                           │ session_id (FK)       │   │
                           │ role (user/assistant) │   │
                           │ content               │   │
                           │ sources (JSON)        │   │
                           │ created_at            │   │
                           └──────────────────────┘   │
                                                       │
                           ┌──────────────────────┐   │
                           │      Scenario        │───┘
                           ├──────────────────────┤
                           │ id (PK, UUID)         │
                           │ name                  │
                           │ description           │
                           │ system_prompt         │
                           │ is_default            │
                           │ created_at            │
                           └──────────────────────┘
```

### Các bảng

| Bảng | Mô tả |
|---|---|
| `documents` | Metadata tài liệu đã upload (không lưu nội dung — nội dung ở ChromaDB) |
| `scenarios` | Template system prompt, hỗ trợ biến Jinja2 `{{ documents }}` |
| `chat_sessions` | Phiên chat, liên kết nhiều tài liệu + 1 kịch bản |
| `session_documents` | Bảng N-N giữa session và document |
| `messages` | Lịch sử chat, lưu cả nguồn tham khảo (JSON) |

---

## Cài đặt

### Yêu cầu

- Python 3.9+
- [Ollama](https://ollama.com) đang chạy với model `gemma4:e4b`

```bash
# Cài Ollama (macOS)
curl -fsSL https://ollama.com/install.sh | sh

# Tải model
ollama pull gemma4:e4b

# Khởi động Ollama (Terminal 1)
ollama serve
```

### Cài đặt project

```bash
# Clone repo
git clone https://github.com/<your-username>/docmind ~/docmind
cd ~/docmind

# Tạo môi trường ảo
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt

# Cấu hình
cp .env.example .env              # Chỉnh sửa nếu cần
```

### Khởi động (Terminal 2)

```bash
cd ~/docmind
python3 run.py
```

Mở trình duyệt: **http://localhost:7860**

---

## Cấu hình

| Biến | Mặc định | Mô tả |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Địa chỉ Ollama server |
| `MODEL_NAME` | `gemma4:e4b` | Model LLM |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model (tự download) |
| `APP_PORT` | `7860` | Port web app |
| `DEFAULT_TOP_K` | `5` | Số chunks lấy khi RAG |
| `CHUNK_SIZE` | `1500` | Kích thước mỗi chunk (ký tự) |
| `CHUNK_OVERLAP` | `200` | Overlap giữa các chunk |
| `MAX_TOKENS` | `2048` | Giới hạn token output |
| `TEMPERATURE` | `0.7` | Độ sáng tạo của model |

---

## Sử dụng

1. **Upload tài liệu** — vào `/documents`, kéo thả PDF/DOCX/TXT. Chờ trạng thái chuyển thành **Sẵn sàng**.

2. **Tạo kịch bản** _(tuỳ chọn)_ — vào `/scenarios`, tạo system prompt tuỳ chỉnh. Dùng `{{ documents }}` để inject danh sách tài liệu vào prompt.

3. **Tạo phiên chat** — nhấn **+** trên sidebar, đặt tên, chọn kịch bản, tích tài liệu muốn hỏi.

4. **Chat** — gõ câu hỏi, Enter để gửi. AI trả lời realtime kèm nguồn tham khảo (tên file + trang).

### Kiểm tra hệ thống

```bash
curl http://localhost:7860/api/v1/health
# {"status":"ok","ollama":{"ok":true,"models":["gemma4:e4b"]},"chromadb":true,"embedding_model":true}
```

Swagger UI: **http://localhost:7860/docs**

---

## Kiến trúc dữ liệu — ChromaDB

Mỗi chunk trong ChromaDB mang metadata:

```json
{
  "document_id": "uuid",
  "source": "filename.pdf",
  "page": 1
}
```

Khi query, filter theo `document_id ∈ {ids của tài liệu trong session}` để đảm bảo chỉ tìm trong tài liệu được chọn.

---

## License

MIT
