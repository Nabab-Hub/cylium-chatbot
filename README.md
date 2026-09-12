# 🤖 CyliumOS RAG Chatbot API (Groq & Gemini)

An enterprise-grade, high-throughput conversational AI chatbot microservice built with **FastAPI**, **Groq** (`qwen/qwen3.6-27b`), **Google Gemini** (`google-genai` SDK), and real-time **Firebase Firestore** for dynamic RAG (Retrieval-Augmented Generation) and hybrid session persistence.

The chatbot provides authoritative, accurate answers about the entire **CyliumOS (SAS)** ecosystem: services, deep learning vision models, transparent pricing plans, universal API keys, billing, policies, and code integrations.

---

## 🌟 Key Features

1. **Dual LLM Provider Support**:
   - **Groq Engine**: Ultra-low-latency text generation via `qwen/qwen3.6-27b` (ideal for instantaneous real-time streaming).
   - **Google Gemini Engine**: Powered by `gemini-2.5-flash` or `gemini-3.7-flash` via official `google-genai` SDK.
   - Switch seamlessly using the `LLM_PROVIDER` environment variable (`groq` or `gemini`).

2. **Dynamic RAG (Retrieval Augmented Generation)**:
   - Synchronizes live platform state from Cloud Firestore (`services` and `plans` collections).
   - Injects real-time user context (active subscriptions, quota usage, API key environments) when an authenticated user chats.
   - Comprehensive embedded platform knowledge base covering all policies, routes, and SDK snippets.

3. **Hybrid Intelligent Session Management**:
   - **Logged-in Users** (`user_id` supplied):
     - Automatically creates and synchronizes sessions in Firestore (`chatSessions` and `chatMessages`).
     - Loads previous multi-turn chat history from Firebase to maintain coherent context.
   - **Guest / Anonymous Users**:
     - Maintains current session state purely in-memory.
     - **Zero Firebase footprint** for anonymous users, protecting privacy and preventing database clutter.

4. **Streaming & Synchronous Modes**:
   - Standard synchronous JSON output with interactive action chips.
   - Real-time Server-Sent Events (SSE) streaming for responsive token-by-token web widgets.

5. **Production Docker Ready**:
   - Lightweight `python:3.11-slim` container with built-in health checks and graceful fallback.
   - Pre-configured `docker-compose.yml`.

---

## 📁 Directory Structure

```
ai-models/chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory, CORS, lifespan, router mounting
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py              # User authentication & token extraction
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── chat.py          # /api/v1/chat (sync & SSE), sessions endpoints
│   │       └── health.py        # /health and / service info
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Pydantic BaseSettings loading from .env
│   │   └── constants.py         # CyliumOS Master Knowledge Base & system prompts
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic request & response schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── firebase.py          # Firestore connection, services, plans, and session sync
│   │   ├── gemini.py            # Google GenAI client (google-genai) with streaming
│   │   ├── groq_client.py       # Groq client (qwen/qwen3.6-27b) with streaming
│   │   ├── llm_factory.py       # Provider selector (groq vs gemini)
│   │   ├── rag.py               # RAG context builder: merges live Firestore data + static knowledge
│   │   └── session_manager.py   # Hybrid session manager (Firebase for auth, in-memory for guests)
│   └── utils/
│       ├── __init__.py
│       └── helpers.py           # Action matcher, title summarizer, timestamps
├── .dockerignore
├── .env.example
├── .env
├── .gitignore
├── Dockerfile                   # Production container
├── docker-compose.yml           # Docker Compose file
├── requirements.txt             # Python dependencies
├── test_chatbot.py              # End-to-end verification script
└── README.md                    # Documentation
```

---

## ⚙️ Environment Configuration (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_PROVIDER` | No | `groq` | Active LLM engine: `groq` or `gemini`. |
| `GROQ_API_KEY` | If using Groq | — | Groq API Key (`gsk_...`). |
| `GROQ_MODEL` | No | `qwen/qwen3.6-27b` | Groq model identifier. |
| `GEMINI_API_KEY` | If using Gemini | — | Google AI Studio Gemini API Key. |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Gemini model (`gemini-2.5-flash`, `gemini-3.7-flash`). |
| `FIREBASE_PROJECT_ID` | No | `nude-checker` | Firebase Project ID. |
| `FIREBASE_CREDENTIALS` | No | `""` | Path to service account credentials JSON. |
| `FIREBASE_SERVICE_ACCOUNT_JSON`| No | `""` | Optional raw JSON string for containers. |
| `HOST` | No | `0.0.0.0` | Server bind host. |
| `PORT` | No | `8002` | Server bind port. |
| `RAG_CACHE_TTL_SECONDS` | No | `120` | Cache duration for Firestore services & plans. |
| `ANONYMOUS_SESSION_TTL_SECONDS`| No | `3600` | In-memory session expiry for guest users. |

---

## 📡 API Endpoints Reference

### 1. Health Check (`GET /health`)
Returns chatbot health, active LLM provider, and Firebase connectivity.

#### Request:
```bash
curl -X GET "http://localhost:8002/health"
```

#### Response (`200 OK`):
```json
{
  "status": "healthy",
  "service": "cyliumos-chatbot-api",
  "version": "1.0.0",
  "llm_provider": "groq",
  "model": "qwen/qwen3.6-27b",
  "llm_ready": true,
  "firebase_connected": true,
  "timestamp": 1726071400000
}
```

---

### 2. Submit Chat Message (`POST /api/v1/chat`)

#### Request Body Schema:
| Field | Type | Required | Description |
|---|---|---|---|
| `message` | string | Yes | The user question or query. |
| `session_id` | string | No | Omit to initialize a new session, or pass existing ID to continue. |
| `user_id` | string | No | User ID. When provided, session & history are stored in Firestore. |
| `stream` | boolean | No | Set `true` for SSE token-by-token streaming. Default `false`. |
| `include_history` | boolean | No | Whether to include prior conversational context. Default `true`. |

---

#### A. Guest / Anonymous User (Synchronous JSON)
```bash
curl -X POST "http://localhost:8002/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What services does CyliumOS offer and how does billing work?"
  }'
```

**Response (`200 OK`):**
```json
{
  "success": true,
  "session_id": "cs_9f83a2bc104de712",
  "response": "CyliumOS provides an enterprise suite of AI microservices:\n\n1. **NSFW & Visual Safety Detector** (/services/nsfw-detection)\n2. **Image Enhancer & Super-Resolution** (/services/image-enhancer)\n3. **Object Visibility & Quality Detection** (/services/visibility-detection)\n\n### Pricing Plans:\n- **Free**: $0/mo (500 requests)\n- **Pro**: $29/mo (50,000 requests)\n- **Enterprise**: Custom high-volume access.",
  "user_id": null,
  "is_authenticated": false,
  "actions": [
    {"label": "Explore All Services", "to": "/services"},
    {"label": "View Pricing & Plans", "to": "/pricing"},
    {"label": "Developer Documentation", "to": "/docs"}
  ],
  "timestamp": 1726071405000
}
```

---

#### B. Authenticated User (Persisted in Firestore)
```bash
curl -X POST "http://localhost:8002/api/v1/chat" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: user_982734" \
  -d '{
    "session_id": "cs_9f83a2bc104de712",
    "message": "How many API requests do I have left this month?"
  }'
```

---

#### C. Real-Time Streaming Mode (Server-Sent Events)
```bash
curl -N -X POST "http://localhost:8002/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain the zero-retention privacy policy.",
    "stream": true
  }'
```

**Stream chunks output:**
```
data: {"type": "start", "session_id": "cs_9f83a2bc104de712"}

data: {"type": "token", "content": "CyliumOS "}

data: {"type": "token", "content": "strictly enforces "}

data: {"type": "token", "content": "zero-retention."}

data: {"type": "done", "actions": [{"label": "Privacy Policy", "to": "/privacy"}]}
```

---

### 3. List User Sessions (`GET /api/v1/chat/sessions`)
*(Requires `X-User-Id` header)*

```bash
curl -X GET "http://localhost:8002/api/v1/chat/sessions" \
  -H "X-User-Id: user_982734"
```

---

### 4. Delete Session (`DELETE /api/v1/chat/sessions/{session_id}`)

```bash
curl -X DELETE "http://localhost:8002/api/v1/chat/sessions/cs_9f83a2bc104de712" \
  -H "X-User-Id: user_982734"
```

---

## 💻 SDK & Client Integration Examples

### JavaScript / TypeScript (Streaming Fetch Widget)

```typescript
async function streamChat(message: string, sessionId?: string, onToken?: (token: string) => void) {
  const response = await fetch("http://localhost:8002/api/v1/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      stream: true,
    }),
  });

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  let fullText = "";

  if (!reader) return;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const lines = decoder.decode(value).split("\n");
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const payload = JSON.parse(line.slice(6));
          if (payload.type === "token" && payload.content) {
            fullText += payload.content;
            onToken?.(payload.content);
          }
        } catch {}
      }
    }
  }

  return fullText;
}

// Example usage
streamChat("What is CyliumOS?", undefined, (chunk) => process.stdout.write(chunk));
```

### Python (`requests`)

```python
import requests

API_URL = "http://localhost:8002/api/v1/chat"

payload = {
    "message": "Give me a quick overview of all models available on CyliumOS.",
    "stream": False,
}

response = requests.post(API_URL, json=payload)
if response.status_code == 200:
    data = response.json()
    print("Session ID:", data["session_id"])
    print("Response:\n", data["response"])
    print("Suggested Actions:", [a["label"] for a in data.get("actions", [])])
else:
    print(f"Error {response.status_code}:", response.json())
```

---

## 🚨 Error Codes & Troubleshooting

All API error responses follow standard HTTP status codes and provide a consistent error body:

```json
{
  "success": false,
  "error": "error_identifier_code",
  "message": "Human readable description of the error"
}
```

### Error Summary Table

| HTTP Status | Error Code (`error`) | Description & Cause | Resolution |
|---|---|---|---|
| **`400 Bad Request`** | `empty_message` | The `message` field is missing, whitespace-only, or too short. | Provide a non-empty text string in `message`. |
| **`401 Unauthorized`** | `unauthorized` | Missing user identity on a session management endpoint. | Supply the `X-User-Id` header or authorization token. |
| **`403 Forbidden`** | `forbidden_session` | Attempted to access or delete another user's session. | Verify that `X-User-Id` matches the session owner. |
| **`404 Not Found`** | `session_not_found` | Specified `session_id` does not exist or has expired. | Omit `session_id` to start a new chat session. |
| **`429 Too Many Requests`**| `rate_limit_exceeded` | Client exceeded IP or session request rate limit. | Wait a few seconds before retrying requests. |
| **`500 Internal Error`** | `internal_error` | Unexpected server exception or parsing failure. | Check server logs (`docker compose logs -f`). |
| **`502 Bad Gateway`** | `llm_provider_error` | Groq or Google Gemini API returned an error or timed out. | Check `GROQ_API_KEY` / `GEMINI_API_KEY` and upstream status. |
| **`503 Unavailable`** | `firebase_unavailable`| Firestore connection error while fetching live RAG data. | Chatbot falls back to embedded knowledge; verify credentials. |

---

### Error Response Samples

#### 1. Empty Message (`400 Bad Request`)
```json
{
  "success": false,
  "error": "empty_message",
  "message": "The message field cannot be empty"
}
```

#### 2. Session Not Found (`404 Not Found`)
```json
{
  "success": false,
  "error": "session_not_found",
  "message": "Chat session cs_nonexistent does not exist"
}
```

#### 3. LLM Upstream Timeout (`502 Bad Gateway`)
```json
{
  "success": false,
  "error": "llm_provider_error",
  "message": "Upstream LLM generation failed: connection timeout"
}
```

---

## 🏃 Running Locally

### 1. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
# Set GROQ_API_KEY, GEMINI_API_KEY, and FIREBASE_PROJECT_ID
```

### 4. Start Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

---

## 🐳 Running with Docker

### Using Docker Compose
```bash
docker compose up -d --build
```

### Using Plain Docker
```bash
docker build -t cyliumos-chatbot:latest .
docker run -d \
  --name cyliumos-chatbot \
  -p 8002:8002 \
  --env-file .env \
  cyliumos-chatbot:latest
```

---

## 🧪 Testing

Run the automated test script to verify both RAG knowledge retrieval and chat completion:

```bash
python test_chatbot.py
```
