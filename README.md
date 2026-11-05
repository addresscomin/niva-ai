# NIVA AI: Natural Intelligent Virtual Agent

NIVA AI is a complete, modular, independent AI assistant platform engineered with a responsive web interface, Python FastAPI microservices, and an enterprise Supabase backend.

---

## 1. System Architecture & Directory Structure

```
niva-ai/
├── run_niva.py                    # Unified single-command launcher
├── frontend/                      # Responsive Web Application (PC & Mobile)
│   ├── index.html                 # Single Page Application entry
│   ├── manifest.json              # Android PWA manifest
│   ├── css/
│   │   ├── main.css               # Deep charcoal theme & base styles
│   │   ├── layout.css             # Responsive desktop sidebar & mobile navigation
│   │   ├── chat.css               # AI Brain workspace & streaming markdown
│   │   ├── voice.css              # Voice visualizer, mic orb & TTS controls
│   │   ├── phone.css              # Android phone control & approval cards
│   │   ├── media.css              # Image & Video generation studio
│   │   ├── files.css              # Storage upload & document analysis
│   │   ├── automation.css         # n8n & MCP workflow dashboard
│   │   └── settings.css           # Profile, preferences & memory management
│   └── js/
│       ├── config.js              # Supabase URL & publishable keys (No secrets)
│       ├── supabaseClient.js      # Supabase JS client integration
│       ├── auth.js                # Supabase Auth manager (Email/Password, Sessions)
│       ├── app.js                 # Core SPA routing & event coordinator
│       ├── chat.js                # AI Brain, multi-model streaming, memory injection
│       ├── voice.js               # Web Speech STT, audio canvas, TTS synth
│       ├── phoneBridge.js         # Android bridge protocol & approval gates
│       ├── mediaStudio.js         # Pollinations / HuggingFace diffusion studio
│       ├── filesManager.js        # Supabase Storage bucket upload & AI analysis
│       ├── automations.js         # n8n webhook dispatcher & MCP tool caller
│       └── settings.js            # Long-term memory controls & profile preferences
├── backend/                       # Python FastAPI Microservices
│   ├── requirements.txt           # Lightweight, zero-bloat dependencies
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py              # Environment configuration & zero-leak guardrails
│   │   ├── main.py                # FastAPI app with static frontend mounting
│   │   ├── routers/
│   │   │   ├── ai_chat.py         # Streaming SSE & chat completion endpoints
│   │   │   ├── phone_bridge.py    # WebSocket & REST Android bridge
│   │   │   ├── automation.py      # n8n webhooks & MCP tool invocation
│   │   │   └── files.py           # Document analysis & code inspector
│   │   ├── services/
│   │   │   └── ai_providers.py    # Multi-provider adapter (Gemini, Claude, GPT, Groq)
│   │   └── utils/
│   └── tests/
│       ├── test_backend.py        # Complete unit test suite (All Passed)
│       ├── test_chat_streaming.py # Real-time streaming test (Passed)
│       └── test_supabase_integration.py # Supabase REST & RLS test (Passed)
└── supabase/
    └── migrations/
        └── 20261103000000_niva_core_schema.sql  # Database schema & storage policies
```

---

## 2. Supabase Integration & Security Model

The project is integrated directly with the connected Supabase project (`gmklwdzpbntixhvbvfcl`):

- **Database:** PostgreSQL 17.11
- **Row Level Security (RLS):** Enabled and enforced on 100% of exposed tables.
- **Private Storage:** Dedicated `niva-files` bucket with path-isolated user access (`(select auth.uid())::text = (storage.foldername(name))[1]`).
- **Key Safety:** Public client uses publishable keys only (`sb_publishable_...`). Service-role secrets are never exposed in browser code.

### Database Tables:
| Table Name | Description | RLS Policy |
| :--- | :--- | :--- |
| `public.profiles` | User profiles, display name, instructions | `(select auth.uid()) = id` |
| `public.chats` | Conversation threads & mode tracking | `(select auth.uid()) = user_id` |
| `public.messages` | Multi-turn message history with model metadata | `(select auth.uid()) = user_id` |
| `public.niva_memories` | Long-term memory records with user controls | `(select auth.uid()) = user_id` |
| `public.niva_files` | Metadata for uploaded documents in storage | `(select auth.uid()) = user_id` |
| `public.niva_generations`| Image & video creation history | `(select auth.uid()) = user_id` |
| `public.niva_device_actions`| Android phone bridge approval & audit logs | `(select auth.uid()) = user_id` |
| `public.niva_automations` | n8n & MCP workflow definitions | `(select auth.uid()) = user_id` |
| `public.niva_automation_logs` | Real-time execution logs & outputs | `(select auth.uid()) = user_id` |
| `public.niva_settings` | User voice, model, and device settings | `(select auth.uid()) = user_id` |

---

## 3. Features & Functional Verification

### A. AI Brain
- Multi-provider support (Gemini, Claude, GPT-4o, Groq, Pollinations free brain).
- Modes: General Chat, Architecture & Coding, Deep Research.
- Automatic long-term memory retrieval and injection into system prompts.
- Streaming responses with real-time markdown and syntax code blocks.

### B. Voice Assistant
- Tap-to-talk microphone using Web Speech Recognition.
- Real-time HTML5 audio waveform canvas visualizer.
- Text-to-Speech synthesis with voice, pitch, and speed adjustments.
- Instant interrupt/stop speaking button.

### C. Android Phone Control Bridge
- Zero-trust security: No lock-screen bypass, no hidden tracking, zero shell access.
- Safe app launcher grid: WhatsApp, Phone Dialer, Google Maps, Camera, Settings, Gmail, Calendar, YouTube.
- Mandatory user approval modal for all device actions before execution.
- Real-time battery status and network monitoring.

### D. Image & Video Generation
- Prompt builder with aspect ratios (1:1, 16:9, 9:16, 4:3).
- Free, high-fidelity neural image generation via Pollinations AI.
- Video workflow simulator and download capabilities.
- History synchronized directly with Supabase `niva_generations`.

### E. File Management & Research
- Drag-and-drop file upload to private Supabase Storage `niva-files` bucket (up to 50MB).
- Document analysis and code summarization with NIVA Brain.
- Confirmation modal before file deletion.

### F. Automation (n8n & MCP)
- Webhook receiver for n8n workflows (`/api/v1/automation/webhook/{id}`).
- MCP tool invocation dispatcher (`/api/v1/automation/mcp/invoke`).
- Audit logging of all automation triggers in Supabase.

---

## 4. Running NIVA AI Locally

1. **Start the unified platform:**
   ```powershell
   python C:\Users\STUDENT\.gemini\antigravity\scratch\niva-ai\run_niva.py
   ```
2. **Access NIVA:**
   - Web App (PC & Mobile Browser): `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/health`

3. **Run Automated Tests:**
   ```powershell
   python C:\Users\STUDENT\.gemini\antigravity\scratch\niva-ai\backend\tests\test_backend.py
   python C:\Users\STUDENT\.gemini\antigravity\scratch\niva-ai\backend\tests\test_chat_streaming.py
   python C:\Users\STUDENT\.gemini\antigravity\scratch\niva-ai\backend\tests\test_supabase_integration.py
   ```
