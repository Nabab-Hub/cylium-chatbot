"""
CyliumOS Master Knowledge Base and System Prompt Constants.
This provides comprehensive domain knowledge for RAG generation.
"""

SYSTEM_PROMPT = """You are the official AI Assistant for CyliumOS (SAS) — the enterprise-grade AI Cloud Microservices and Developer Infrastructure Platform.
Your purpose is to assist developers, founders, enterprise architects, and site visitors with accurate, authoritative, and helpful answers regarding the CyliumOS platform.

### CORE DIRECTIVES & PERSONA:
1. **Brand Identity**: You represent CyliumOS. You are deeply technical, highly professional, welcoming, and concise yet thorough.
2. **Language Handling**: You can converse fluently in English, Bengali (বাংলা), and Hindi (हिन्दी). If a user asks in Bengali or Banglish, answer naturally in Bengali/Banglish; if in English, answer in English.
3. **Platform Knowledge**: You have complete knowledge of CyliumOS's microservices, AI models, pricing plans, universal API keys, billing, architecture, developer SDKs, security policies, and navigation routes.
4. **Context Awareness**: You will be provided with dynamic RAG context retrieved in real-time from the platform and Firebase (including active services, plans, user subscriptions, remaining request quota, and previous conversation turns). Always prioritize this live context when answering user-specific queries (such as their current plan, remaining usage, or active API keys).
5. **Formatting**:
   - Use clean, modern GitHub Flavored Markdown (bullet points, bold text, code blocks with language tags, tables where appropriate).
   - When referencing website sections, use clear path links (e.g. `/services`, `/services/nsfw-detection`, `/services/chatbot`, `/services/visibility-detection`, `/pricing`, `/docs`, `/playground`, `/dashboard`).
   - When providing code snippets, offer production-ready examples in cURL, Python, or JavaScript/TypeScript.
6. **Honesty & Fallback**: If asked about features or services not offered by CyliumOS, politely clarify what CyliumOS specializes in and provide relevant alternatives available on the platform.
7. **COMPLETION & MEANINGFULNESS MANDATE**:
   - ALWAYS provide complete, fully finished answers. NEVER leave a markdown table, bullet list, code block, or sentence truncated or cut off midway.
   - Answer fully and comprehensively based on the available token budget.
   - At the conclusion of helpful answers, provide 2 to 3 short, relevant suggestive follow-up questions for the developer (e.g. under a **💡 Suggested Next Questions:** section) so they can explore further.
"""

CYLIUMOS_MASTER_KNOWLEDGE = """
# CyliumOS (SAS) Platform Master Knowledge Base

## 1. Executive Platform Overview
- **Name**: CyliumOS (Software as a Service / SAS)
- **Tagline**: High-performance modular software platform, developer infrastructure, and AI microservices API gateway.
- **Technology Stack**:
  - Frontend & Fullstack SSR: Built with TanStack Start, React 19, TypeScript, and Tailwind CSS v4.
  - Runtime & Server Engine: Nitro server engine.
  - Microservices & AI Engines: Python FastAPI with specialized deep learning models (ONNX, PyTorch, Transformer ensembles).
  - Database & Identity: Cloud Firestore and Firebase Authentication with high-efficiency REST caching.
  - Payment Processing: Seamless Razorpay integration (INR UPI, NetBanking, Debit/Credit Cards, and USD International Cards).
  - PDF Invoices: Automated instant GST/VAT tax invoice generation powered by `pdf-lib`.

## 2. Core Active AI Microservices
CyliumOS provides 3 core high-throughput, specialized AI microservices:

### A. NSFW & Visual Content Safety Detection (`/services/nsfw-detection`)
- **Overview**: Ultra-fast automated adult content, nudity, violence, weapons, and suggestive material detector.
- **Latency**: Sub-150ms median response time.
- **Model Engine**: Vision Transformer & Deep CNN Ensemble (NudeNet ONNX engine).
- **Features**:
  - `half_nudity` parameter: Optional filtering for partial/suggestive exposure (swimwear, lingerie) vs fully explicit content.
  - `detection_point`: Returns normalized bounding box coordinates `[ymin, xmin, ymax, xmax]` for automated on-the-fly client-side blurring and censoring.
- **Endpoint**: `https://nsfw.cyliumos.online/is_safe` (proxied via `/api/v1/gateway` or `/api/public/playground`).

### B. RAG AI Chatbot Assistant & Reasoning (`/services/chatbot` or `/services/ai-chatbot`)
- **Overview**: High-throughput conversational and reasoning agent with live platform RAG, code generation, and multi-turn context retention.
- **Latency**: Sub-100ms first token.
- **Model Engines**: Groq (Qwen 2.5 / DeepSeek) & Google Gemini hybrid routing.
- **Endpoint**: `https://cbts.cyliumos.online/api/v1/chat`.

### C. Image Visibility & Optical Quality Inspection (`/services/visibility-detection`)
- **Overview**: Real-time diagnostic evaluation of document photos, IDs, product images, and live captures.
- **Diagnostic Metrics**:
  - Laplacian sharpness variance score (blur threshold: 100.0).
  - Motion blur / focus degradation check.
  - Illumination & low-light underexposure check.
  - Specular glare and hot-spot reflection detector.
  - Framing & margin cut-off border detection.
- **Endpoint**: `https://vgdt.cyliumos.online/detect-visibility`.

### D. Interactive Web Playgrounds (`/playground` and `/services/:slug/playground`)
- Real-time interactive testing interface with Live Telemetry Inspector, millisecond stopwatch, and live visual cards.
- Developers can test prompts or image files directly before writing integration code.

## 3. Transparent Pricing Plans & Billing
CyliumOS offers transparent, predictable pricing tiers per service, plus a platform bundle:

| Plan | Monthly Price | Monthly Request Quota | Rate Limit | Key Features |
| :--- | :--- | :--- | :--- | :--- |
| **Starter** | ₹99 / month | 10,000 requests | 60 req/min | Full API access, telemetry logs, email support |
| **Pro** | ₹499 / month | 100,000 requests | 300 req/min | Priority processing queue, 99.9% uptime SLA, 24/7 support |
| **Enterprise** | ₹1,500 / month | 1,000,000 requests | 1,200 req/min | Highest throughput, custom thresholds, dedicated account manager |
| **All-Access Pro Bundle** | ₹999 / month | 300,000 pooled requests | 600 req/min | Shared access across all 3 AI models |

*Playground Testing Quota*:
- Registered normal accounts receive **5 free test requests per day per model** in the Playground.
- Subscribed / paid accounts get **unlimited testing** in the Playground for the models included in their active subscription.
- (Note: There is no $0 recurring monthly subscription; users test with the 5 free daily playground requests).

*Discounts & Payments*:
- Flat **25% discount** automatically applied on all annual billing cycles!
- Payment Methods: Razorpay checkout supporting UPI (GPay, PhonePe, Paytm), Credit Cards, Debit Cards, NetBanking, and International Cards.

## 4. Authentication & API Key Management
- **Universal API Key**: A single API key grants access across all enabled CyliumOS microservices.
- **Header**: Requests must include the HTTP header:
  `X-API-Key: YOUR_CYLIUMOS_API_KEY`
- **Security Architecture**:
  - Keys are stored in Firestore using irreversible SHA-256 hashes (`keyHash`).
  - Plaintext keys can be securely recovered anytime from the authenticated user dashboard under `/dashboard`.
  - Environment labeling: Support for `production`, `staging`, and `development` tags per key.

## 6. Security, Zero-Retention Privacy, & Compliance
- **Zero-Retention Guarantee**: All uploaded images, video frames, and text inputs are processed purely in ephemeral RAM and instantly discarded upon response delivery.
- **No Training on Customer Data**: Customer data is NEVER logged to disk or used to train or fine-tune public models.
- **Compliance**: Fully compliant with GDPR, HIPAA, and SOC2 principles.
- **Encryption**: TLS 1.3 in transit; AES-256 at rest for account metadata.

## 7. Platform Policies & Customer Protection
- **Refund Policy (`/refund-policy`)**:
  - 5-day money-back guarantee from the transaction date.
  - Eligible if request usage is below 20% of the plan's monthly allocation.
  - Transparent automated audit trail with immutable status tracking (`requested` -> `approved` -> `processing` -> `refunded`).
- **Terms of Service (`/terms`)**: Enterprise SLA commitments, acceptable use policy, API availability guarantees.
- **Privacy Policy (`/privacy`)**: Complete data minimization disclosure and cookie policies.
- **Customer Support (`/contact`)**: Support desk reachable at support@cyliumos.com.

## 8. Integration Examples

### cURL
```bash
curl -X POST "https://api.cyliumos.com/api/v1/gateway" \\
  -H "X-API-Key: cyk_live_your_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"service": "nsfw-detection", "image_url": "https://example.com/photo.jpg"}'
```

### Python
```python
import requests

url = "https://api.cyliumos.com/api/v1/gateway"
headers = {
    "X-API-Key": "cyk_live_your_key_here",
    "Content-Type": "application/json"
}
payload = {
    "service": "nsfw-detection",
    "image_url": "https://example.com/photo.jpg",
    "half_nudity": False
}
response = requests.post(url, headers=headers, json=payload)
print(response.json())
```

### Node.js / TypeScript
```typescript
import axios from 'axios';

const { data } = await axios.post('https://api.cyliumos.com/api/v1/gateway', {
  service: 'nsfw-detection',
  image_url: 'https://example.com/photo.jpg'
}, {
  headers: {
    'X-API-Key': 'cyk_live_your_key_here',
    'Content-Type': 'application/json'
  }
});
console.log(data);
```
"""

# Common suggested quick actions to accompany responses
SUGGESTED_QUICK_ACTIONS = [
    {"label": "Explore Services", "to": "/services"},
    {"label": "Check Pricing", "to": "/pricing"},
    {"label": "Open Playground", "to": "/playground"},
    {"label": "Developer Docs", "to": "/docs"},
    {"label": "Get API Key", "to": "/dashboard"},
    {"label": "Contact Support", "to": "/contact"},
]
