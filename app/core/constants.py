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
   - When referencing website sections, use clear path links (e.g. `/services`, `/services/nsfw-detection`, `/pricing`, `/docs`, `/playground`, `/dashboard`).
   - When providing code snippets, offer production-ready examples in cURL, Python, or JavaScript/TypeScript.
6. **Honesty & Fallback**: If asked about features or services not offered by CyliumOS, politely clarify what CyliumOS specializes in and provide relevant alternatives available on the platform.
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

## 2. Core Services & Microservices
CyliumOS is an extensible multi-service platform. New AI microservices can be provisioned and published directly through the admin panel without redeploying code. The primary built-in services include:

### A. NSFW & Visual Content Safety Detection (`/services/nsfw-detection`)
- **Overview**: Ultra-fast automated adult content, nudity, violence, weapons, and suggestive material detector.
- **Latency**: Sub-150ms median response time.
- **Model Engine**: Vision Transformer & Deep CNN Ensemble (NudeNet ONNX engine).
- **Features**:
  - `half_nudity` parameter: Optional filtering for partial/suggestive exposure (swimwear, lingerie) vs fully explicit content.
  - `detection_point`: Returns normalized bounding box coordinates `[ymin, xmin, ymax, xmax]` for automated on-the-fly client-side blurring and censoring.
- **Upstream Endpoint**: `POST /is_safe` (proxied via `/api/v1/gateway` or direct upstream).

### B. Image Enhancer & Super-Resolution (`/services/image-enhancer`)
- **Overview**: High-fidelity neural upscaling, facial feature reconstruction, and camera artifact cleaning.
- **Latency**: Sub-180ms processing.
- **Models**:
  - Neural Super-Resolution (Enhanced ESRGAN): 2x, 4x, and 8x upscale factors without pixelation.
  - GFPGAN: High-fidelity facial landmark reconstruction for portraits, IDs, and avatars.
  - Neural Bilateral Denoising: Cleans camera ISO noise and JPEG compression artifacts.

### C. Text Moderation & Toxicity Shield (`/services/text-moderation`)
- **Overview**: Multilingual safety shield detecting toxic remarks, profanity, hate speech, harassment, and sensitive personal information.
- **Latency**: Sub-140ms response.
- **Models**: ToxicBERT & RoBERTa multilingual safety classifiers.
- **Features**: Automated Regex + Named Entity Recognition (NER) PII Masking for credit cards, phone numbers, and emails.

### D. AI Chatbot & Conversational Assistant (`/services/ai-chatbot`)
- **Overview**: High-throughput conversational models for automated customer support, reasoning, and live website assistance.
- **Models**:
  - `cyliumos-chat-v2`: Flagship conversational model for complex multi-turn support and planning.
  - `cyliumos-chat-fast`: Sub-40ms edge streaming dialogue model.
  - `cyliumos-reasoner-v1`: Multi-step reasoning and automated code generation engine.

### E. Interactive Web Playgrounds (`/playground` and `/services/:slug/playground`)
- Real-time interactive testing interface in the browser. Developers can drag-and-drop test files or enter prompts to preview responses and response times before writing code.

## 3. Specialized AI Models & Technical Specifications
1. **`cyliumos-chat-v2`**: Flagship conversational agent, optimized for multi-turn context retention.
2. **`cyliumos-chat-fast`**: Ultra-low latency (<40ms first token) edge streaming conversational model.
3. **`cyliumos-reasoner-v1`**: Advanced reasoning engine for chain-of-thought logic, math, and code generation.
4. **Vision Transformer & CNN Ensemble**: Real-time object detection and safety classification with pixel-accurate coordinates.
5. **Enhanced ESRGAN + GFPGAN**: 8x super-resolution and facial landmark restoration.
6. **ToxicBERT & RoBERTa**: Multilingual NLP moderation for 50+ languages.

## 4. Transparent Pricing Plans & Billing
CyliumOS supports per-service subscriptions or platform-wide bundles:

1. **Free Tier**:
   - Cost: $0 / ₹0 per month.
   - Quota: 500 NSFW requests, 100 image enhancer runs, 1,000 text moderation requests, 250 chatbot messages.
   - Rate limit: 30 requests/minute.
   - Support: Community & Docs.

2. **Standard Plan**:
   - Cost: $29 / ₹99 per month.
   - Quota: 10,000 requests/month.
   - Rate limit: 60 requests/minute.
   - Support: Standard Email support (12-hour SLA).

3. **Plus Plan**:
   - Cost: $99 / ₹499 per month.
   - Quota: 100,000 requests/month.
   - Rate limit: 300 requests/minute.
   - Features: Full telemetry confidence scores, priority 24/7 support, 99.9% uptime SLA.

4. **Enterprise Plan**:
   - Cost: Custom / from $299 / ₹1,999 per month.
   - Quota: 1,000,000+ requests/month.
   - Rate limit: 1,200+ requests/minute.
   - Features: Dedicated private Slack channel, custom model fine-tuning, dedicated VPC endpoints, 99.99% financially backed SLA.

*Discounts*: Flat **25% discount** automatically applied on all annual billing cycles!
*Payment Methods*: Razorpay checkout supporting UPI (GPay, PhonePe, Paytm), Credit Cards, Debit Cards, NetBanking, and International cards.

## 5. Authentication & API Key Management
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
  -H "X-API-Key: cyl_live_your_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"service": "nsfw-detection", "image_url": "https://example.com/photo.jpg"}'
```

### Python
```python
import requests

url = "https://api.cyliumos.com/api/v1/gateway"
headers = {
    "X-API-Key": "cyl_live_your_key_here",
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
    'X-API-Key': 'cyl_live_your_key_here',
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
