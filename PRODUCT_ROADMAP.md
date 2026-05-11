# ShopDesk Support — Product Roadmap
### From Portfolio Project to a Product CEOs Will Fight For

> **Current State Analysis:** This document is based on a thorough code review of every file in this repository. It is honest, direct, and prioritised. Every criticism is paired with a concrete recommendation. The goal is to give you a clear, executable path from where the project is today to a product that can be sold to businesses at a premium price.

---

## Table of Contents
1. [Honest Assessment of What You Have](#1-honest-assessment)
2. [Critical Code-Level Fixes (Do These First)](#2-critical-code-level-fixes)
3. [Architecture Upgrades](#3-architecture-upgrades)
4. [Agent & AI Intelligence Improvements](#4-agent--ai-intelligence-improvements)
5. [New Features to Build](#5-new-features-to-build)
6. [Integrations & Omnichannel](#6-integrations--omnichannel)
7. [Dashboard & Frontend](#7-dashboard--frontend)
8. [Observability & Analytics](#8-observability--analytics)
9. [Security & Compliance](#9-security--compliance)
10. [Testing & DevOps](#10-testing--devops)
11. [Phased Execution Plan](#11-phased-execution-plan)

---

## 1. Honest Assessment

### What You Built Well
- Clean 3-layer agent architecture (Router → Orchestrator → Worker) that is genuinely sound.
- Correct use of Pydantic `with_structured_output` for the router — this is the right way to do intent classification.
- Abstract `VectorDBClient` base class in `vectorstore/base.py` — good design, allows swapping vector DBs.
- Proper JWT with both access and refresh tokens, including token-type validation.
- Rate limiting scoped per user, not per IP — the right call for an authenticated API.
- A real knowledge base with detailed, well-structured FAQs — not a placeholder.
- Docker + Alembic migrations + seed data — this is a real, deployable project.

### The Hard Truth: What Is Stopping It From Being a Product
The architecture is a solid prototype. But there is no paying customer who could use this system as-is, because:

1. **There is no frontend** — a CEO cannot demo this to their board. Customers cannot use it.
2. **There is no multi-tenancy** — a second business cannot be onboarded without modifying the code.
3. **There are zero write operations** — the agent can only read data. It can never actually *do* anything for a customer.
4. **The logout endpoint is fake** — it does nothing. Tokens are never invalidated.
5. **The user model is critically incomplete** — missing `created_at`, `is_active`, `email_verified`, and `password_reset_token`.
6. **The escalation system is a stub** — it creates a ticket in a database that no human will ever see in real time.
7. **No streaming** — every chat request blocks HTTP until the full LLM response is generated, causing frequent timeouts in production.
8. **PII is being sent raw to Groq** — `_get_user_context` passes the user's name, email, and phone number directly to an external LLM in plaintext.
9. **Single point of LLM failure** — if Groq has an outage, the entire system goes down.
10. **History is just string concatenation** — `f"User: {msg.content}"` is fragile and the stripping logic (`.replace("User: ", "")`) will silently corrupt messages that start with "User: " as part of their content.

---

## 2. Critical Code-Level Fixes

These are bugs and security issues in the existing code that must be fixed before anything else. They do not require new features — they are corrections to what already exists.

### 2.1 The Logout Endpoint Does Nothing
**File:** `app/routes/auth.py` — line 129

```python
# current — completely broken
@router.post("/logout")
def logout_user(request: Request):
    return {"message": "success"}
```

**Fix:** Implement a token blacklist using Redis. On logout, add the token's `jti` (JWT ID) to a Redis set with a TTL matching the token expiry. On every authenticated request, check if the JTI is blacklisted.

---

### 2.2 PII Being Sent to an External LLM
**File:** `app/agent/orchestrator.py` — line 126, 172

The `_get_user_context` method builds this string and injects it as a `SystemMessage`:
```python
f"name: {user.name}, email: {user.email}, phone-no: {user.phone}, user_id: {user.user_id}"
```

This sends raw PII (email, phone) to Groq (an external third party). For any enterprise customer under GDPR or CCPA, this is a blocker.

**Fix:** Strip sensitive fields. Only send the `user_id` to the LLM. The tools themselves can resolve account data when needed — that is exactly what they are for.

---

### 2.3 History Parsing is Fragile and Will Corrupt Data
**Files:** `orchestrator.py` line 40, `router.py` line 40, `rag_chain.py` line 28

All three files use this pattern to reconstruct `LangChain` messages from database strings:
```python
HumanMessage(content=s.replace("User: ", "")) if s.startswith("User: ") else ...
```

If a user's message is `"User: I need help"`, the prefix strip will turn it into `"I need help"` — but if a user sends `"User: can you help"` the content becomes `"can you help"` losing the original intent. More critically, a user could craft a message beginning with `"Assistant: "` to inject false conversation history.

**Fix:** Store and retrieve messages as structured objects (already done in the DB model via `MessageRole`). Reconstruct `HumanMessage`/`AIMessage` directly from the `role` enum, not by parsing string prefixes. Remove all three `.replace()` calls.

---

### 2.4 UUID Default on the User Model is Evaluated Once at Module Load
**File:** `app/db/models.py` — line 36

```python
# Wrong — uuid4() is called ONCE at import time, all users get the same ID
user_id = Column(PGUUID, primary_key=True, default=uuid.uuid4())

# Correct — lambda ensures a new UUID per row
user_id = Column(PGUUID, primary_key=True, default=lambda: uuid.uuid4())
```

This is a critical data-integrity bug. All other models (`Order`, `Session`, etc.) use the correct `lambda` form — only `User` is broken.

---

### 2.5 The Orchestrator Creates a New Orchestrator Instance Per Request
**File:** `app/dependencies.py` — lines 29–38

```python
def get_orchestrator(db: DBSession = Depends(get_db)) -> Orchestrator:
    orchestrator = Orchestrator(rag=rag, router=router, db=db, tools=[...])
    return orchestrator
```

A new `Orchestrator` object is created on every single HTTP request. While the `rag` and `router` singletons are reused, the `tools` list is recreated each time, and a new `ChatGroq` LLM client is instantiated in `Orchestrator.__init__` (line 27). This is wasteful. The LLM client should be a shared singleton. Only the `db` session needs per-request scoping.

---

### 2.6 Error Messages Reveal Internal State
The error responses are too informative:
- `"no account found with theese loging details"` — reveals that no account exists, enabling user enumeration.
- `"incorrect password"` — confirms the account exists but the password is wrong.

**Fix:** Return a generic `"invalid email or password"` for all authentication failures.

---

### 2.7 Escalation Ticket `reason` Field Too Short
**File:** `app/db/models.py` — line 71

```python
reason = Column(String(100), nullable=False)
```

A customer complaint can easily exceed 100 characters, causing truncation or an unhandled DB error. Change to `Text`.

---

### 2.8 RAG Retrieval Uses Only 3 Chunks With No Score Threshold
**File:** `app/vectorstore/pinecone_client.py` — line 87 (`top_k=3`)

There is no similarity score threshold. A query that does not exist in the knowledge base will still retrieve the 3 "closest" vectors — which could be completely irrelevant — and the LLM will hallucinate an answer from garbage context.

**Fix:** Filter retrieved chunks by a minimum cosine similarity score (e.g., `score >= 0.70`) before passing to the LLM. If no chunks pass the threshold, explicitly inform the LLM that no relevant context was found.

---

## 3. Architecture Upgrades

### 3.1 Multi-Tenancy (The Most Critical Feature for B2B)
**Current:** The entire system is single-tenant. Every table is shared globally. There is no concept of a "business" or "organisation".

**What this means:** You cannot onboard a second customer without deploying a separate instance.

**Implementation:**
1. Add an `Organisation` table with fields: `org_id`, `name`, `plan` (free/pro/enterprise), `api_key`, `created_at`.
2. Add `org_id` as a foreign key to `User`, `Order`, `Session`, `EscalationTicket`, and `Message`.
3. Every database query must filter by `org_id`.
4. The Pinecone namespace (already configurable) becomes `org_{org_id}` — each business gets its own isolated vector space.
5. All API endpoints derive `org_id` from the authenticated user's token — it should never be user-supplied.

---

### 3.2 Streaming Responses (WebSocket or Server-Sent Events)
**Current:** The chat endpoint blocks the HTTP connection for 3–8 seconds while waiting for the full LLM response.

**Impact:** In production, API gateways (AWS ALB, Nginx) and mobile clients will timeout. Users will see a loading spinner and assume the product is broken.

**Implementation:**
1. Change `app/routes/chat.py` to return a `StreamingResponse` using FastAPI's built-in support.
2. Use LangChain's `.astream()` method on all chains instead of `.invoke()`.
3. Stream tokens as Server-Sent Events (SSE) in the format `data: {token}\n\n`.
4. Make the entire orchestrator async (`async def handle`, `async def _handle_tool_call`, etc.).
5. Replace all synchronous DB calls with `SQLAlchemy` async sessions (`AsyncSession`).

---

### 3.3 Async Everything
**Current:** All agent methods, DB queries, and route handlers are synchronous. FastAPI runs sync functions in a thread pool, limiting throughput significantly.

**Implementation:** Migrate to `async def` across the board:
- `app/routes/chat.py`, `sessions.py`, `queue.py`, `auth.py`
- `app/agent/orchestrator.py`, `router.py`, `rag_chain.py`
- `app/db/database.py` → use `AsyncSession` from `sqlalchemy.ext.asyncio`

---

### 3.4 Redis for Caching and Distributed Rate Limiting
**Current:** Rate limiting via `slowapi` is in-memory and does not work correctly across multiple FastAPI worker processes or horizontally scaled instances.

**Implementation:**
1. Add Redis as a dependency (Docker Compose service).
2. Configure `slowapi` to use Redis as its storage backend.
3. Cache frequent non-mutating DB queries (e.g., user profile lookups) with a short TTL (60s).
4. Use Redis for the token blacklist (see Section 2.1).
5. Use Redis for distributed session locking to prevent race conditions in concurrent chat requests for the same session.

---

### 3.5 Background Task Queue
**Current:** All processing happens synchronously in the request/response cycle. Any LLM call failure means the user gets an error with no retry.

**Implementation:** Introduce Celery + Redis (or ARQ for a simpler async alternative) for:
- Proactive notification jobs (delayed shipment alerts, follow-up messages).
- Background knowledge base ingestion when a business uploads a document.
- Async ticket notification emails to human agents on escalation.
- Retry logic for failed LLM calls.

---

## 4. Agent & AI Intelligence Improvements

### 4.1 LLM Fallback Chain (Model Routing)
**Current:** The system has a single hard dependency on Groq. A Groq outage means zero availability.

**Implementation:** Build a `LLMRouter` class that wraps multiple providers with fallback:
```
Primary: Groq (llama-3.1-8b) — fastest, cheapest
Fallback 1: OpenAI (gpt-4o-mini) — reliable
Fallback 2: Anthropic (claude-haiku) — high availability
```
Catch API exceptions and rate-limit errors, then automatically retry with the next provider. Log which model was used per request for cost analysis.

---

### 4.2 Agentic Write Operations (Mutations)
**Current:** The three tools (`get_order_status`, `get_recent_orders`, `get_account_info`) are all read-only. The agent is purely an information-fetcher, not an autonomous support agent.

**New tools to build:**
- `initiate_return(order_id, reason)` — creates a return record and generates a return label.
- `cancel_order(order_id)` — cancels an order if it is still in `PENDING` status.
- `update_shipping_address(order_id, new_address)` — modifies the address within the 2-hour window.
- `apply_coupon(order_id, coupon_code)` — validates and applies discounts retroactively.
- `send_escalation_notification(ticket_id)` — triggers an email/Slack notification to the human agent queue.

**Critical:** Each write tool must include a confirmation step. The agent should present the intended action to the user and ask for explicit confirmation before executing any mutation.

---

### 4.3 Sentiment Analysis & Dynamic Tone Shifting
**Current:** The agent responds identically regardless of whether the user is happy, neutral, or furious.

**Implementation:**
1. Before routing, run a lightweight sentiment classifier on the user's message (can be a fast LLM call or a local model like `cardiffnlp/twitter-roberta-base-sentiment`).
2. Store sentiment score on the `Message` model.
3. Add a `SentimentLevel` enum: `POSITIVE`, `NEUTRAL`, `FRUSTRATED`, `ANGRY`.
4. Inject the detected sentiment into the system prompt context. For `FRUSTRATED` and `ANGRY`, automatically lower the escalation threshold in the router prompt and switch the response tone to a more empathetic, apologetic register.
5. If the user has been `FRUSTRATED` for 3+ consecutive messages, auto-escalate without waiting for an explicit escalation trigger.

---

### 4.4 RAG Pipeline Upgrades
**Current:** Flat similarity search → 3 raw text chunks → LLM. No re-ranking, no citations, no score filtering.

**Improvements:**
1. **Score threshold:** As described in Section 2.8. Drop irrelevant chunks.
2. **Re-ranking:** After Pinecone retrieves top-K candidates, pass them through a cross-encoder re-ranker (Cohere Rerank API or a local `cross-encoder/ms-marco-MiniLM-L-6-v2` model) to re-sort by actual relevance. Retrieve top-10, rerank, take top-3.
3. **Citations:** Modify the RAG prompt and response schema to require the LLM to cite which section of the knowledge base it used. Return citations as structured metadata alongside the response text.
4. **Hybrid Search:** Combine dense vector search with BM25 keyword search (Pinecone supports this natively via sparse-dense vectors). This is critical for domain-specific terms like product codes, order IDs, and brand names that semantic search handles poorly.
5. **Contextual chunking:** The current `chunk_size=500` with `chunk_overlap=50` is a generic setting. For the FAQ format (question → answer), use a parent-child chunking strategy: embed the question to retrieve the correct FAQ entry, but send the full Q+A pair as context to the LLM.

---

### 4.5 Conversation Memory Upgrade
**Current:** History is limited to the last 10 messages (hardcoded), reconstructed as plain strings.

**Improvements:**
1. Remove the hardcoded `limit=10`. Make the window configurable via an env variable.
2. Implement a rolling summary: once a conversation exceeds N turns, use an LLM to compress older turns into a summary, which is prepended to the history window. This prevents token limits from silently truncating context.
3. Fix the string-prefix parsing bug (see Section 2.3).
4. Add cross-session memory: if a user returns in a new session, load a brief summary of their last session to provide continuity.

---

### 4.6 Multimodal Support (Image Understanding)
**Current:** Text only.

**Implementation:**
1. Add an `images` optional field to `ChatRequest` (base64-encoded or S3 pre-signed URL).
2. If images are present, route through a vision-capable model (GPT-4o or Llama 3.2 Vision via Groq).
3. Use cases: damaged product photos, screenshots of error messages, photos of wrong items received.
4. Store image references (S3 URLs) in the `Message` model, not the image data itself.

---

### 4.7 Language Detection & Multilingual Support
**Current:** English only.

**Implementation:**
1. Use `langdetect` or `fasttext` language identification on each incoming message.
2. If non-English is detected: translate the query to English before embedding and RAG retrieval (to match the English knowledge base), then translate the English response back to the user's language.
3. Use a dedicated translation LLM call or a translation API (DeepL, Google Translate).
4. Store the detected `language_code` on the `Message` model.

---

## 5. New Features to Build

### 5.1 Real-Time Human Agent Dashboard (Priority: Critical)
**Current:** Escalation tickets are written to a Postgres table. No human ever sees them in real time.

**What to build:** A web-based dashboard (Next.js/React) for human support agents:
- Live queue of escalated tickets, sorted by severity and wait time.
- Click a ticket to open the full conversation transcript.
- **Live Takeover:** Human agent can "claim" a ticket and join the chat via WebSocket, with the customer's interface seamlessly transitioning from AI to human.
- Internal notes and ticket tagging.
- Ticket resolution and closure.
- Agent availability status (online/busy/offline).

This single feature is what transforms the product from a toy into a real support platform.

---

### 5.2 Tenant Admin Dashboard
**What to build:** A separate web portal for the business (the paying customer) to:
- Upload and manage their knowledge base documents (PDF, DOCX, HTML, Markdown).
- View their AI analytics (ticket deflection rate, average resolution time, CSAT scores).
- Configure their AI agent persona (name, tone, escalation triggers).
- Manage their human agent team (invite agents, set roles).
- View and export billing and usage data (tokens consumed, cost per month).

---

### 5.3 Knowledge Base Management API
**Current:** Knowledge base ingestion is a manual, developer-only script (`ingest.py`).

**What to build:**
- `POST /knowledge-base/upload` — accept PDF, DOCX, TXT, Markdown files.
- `GET /knowledge-base/documents` — list all indexed documents with metadata.
- `DELETE /knowledge-base/documents/{doc_id}` — remove a document and its vectors from Pinecone.
- `POST /knowledge-base/sync` — trigger a re-ingestion of all documents.
- Process uploaded files as background tasks (Celery).
- Track which vectors belong to which document for precise deletion.
- Expose ingestion status (queued → processing → complete → error).

---

### 5.4 Proactive Support Engine
**Current:** Purely reactive — the agent only responds when spoken to.

**What to build:**
- A Celery scheduled job that periodically checks for orders that are delayed beyond their estimated delivery date.
- Automatically initiates an outbound message to affected customers via their preferred channel (email, in-app chat).
- Monitors for failed payment retries, subscription expirations, or other state-change events in the business's data.
- Provides an API for the business to trigger proactive notifications: `POST /proactive/notify` with a customer segment filter and message template.

---

### 5.5 Customer Satisfaction (CSAT) Collection
**What to build:**
- At the end of every resolved conversation, the agent sends a CSAT prompt: `"Was I helpful today? 👍 / 👎"` or a 1–5 star rating.
- Store CSAT scores linked to the session, agent (AI or human), and intent type.
- Expose aggregate CSAT in the analytics dashboard.
- Use CSAT data to identify knowledge base gaps (low CSAT on RAG answers → those topics need better documentation).

---

### 5.6 Webhook System for Businesses
**What to build:**
- Allow businesses to register webhook URLs.
- Emit events to the webhook on key actions: `conversation.escalated`, `ticket.resolved`, `csat.received`, `agent.takeover`.
- Standard delivery guarantees: retry with exponential backoff on failure, delivery logs, dead-letter queue.
- Webhook signature verification (HMAC-SHA256 header) so the business can verify events are genuinely from ShopDesk Support.

---

### 5.7 Embeddable Chat Widget
**What to build:**
- A JavaScript snippet (like Intercom) that any business can paste into their website.
- The widget opens a chat window, creates a session, and communicates with the ShopDesk Support API.
- Branded per tenant (logo, color, agent name).
- Mobile-responsive.
- Initialises with context (e.g., the current page, the logged-in user's ID from the host app).

---

### 5.8 Password Reset Flow
**Current:** There is a `"Forgot Password"` reference in the FAQ knowledge base, but no such endpoint exists in the API.

**What to build:**
- `POST /auth/forgot-password` — accept email, generate a signed reset token, send reset email.
- `POST /auth/reset-password` — accept token + new password, validate token, update hash, invalidate all active sessions.
- Add `password_reset_token` and `password_reset_expires` columns to `User`.

---

### 5.9 Email Verification
**Current:** Users register with an email and are immediately granted full access. There is no email verification, meaning anyone can register with `ceo@apple.com`.

**What to build:**
- On registration, set `email_verified = False` and send a verification email with a signed token.
- `GET /auth/verify-email?token=...` — validates the token and sets `email_verified = True`.
- Restrict access to chat endpoints for unverified users.

---

## 6. Integrations & Omnichannel

### 6.1 WhatsApp Integration (Meta Business API)
The highest-value integration for e-commerce support. Most customers in emerging markets primarily use WhatsApp, not web chat.

**Implementation:**
- Set up a Meta Business webhook endpoint: `POST /webhooks/whatsapp`.
- Parse incoming messages, map them to a session (keyed by phone number + `org_id`), and route through the Orchestrator.
- Send responses back via the WhatsApp Business API.
- Handle media messages (images → multimodal support).

---

### 6.2 Email Support via Inbound Parser
**Implementation:**
- Integrate with SendGrid Inbound Parse or Postmark's inbound email processing.
- Parse inbound emails, extract the customer's email, subject, and body.
- Route through the Orchestrator as a new session.
- Reply via outbound email using the same thread's `Message-ID`.

---

### 6.3 Zendesk / Freshdesk Integration
When a ticket is escalated, it should appear in the business's existing helpdesk — not just in the ShopDesk Postgres DB.

**Implementation:**
- On escalation, call the Zendesk API (or Freshdesk, Intercom) to create a ticket with full conversation transcript.
- When the ticket is resolved in Zendesk, sync the status back to ShopDesk via Zendesk's webhook.
- Store the external ticket ID on `EscalationTicket` (`external_ticket_id` column).

---

### 6.4 Slack Integration for Internal Notifications
**Implementation:**
- When a ticket is escalated, post a formatted message to a configured Slack channel.
- Include customer summary, conversation excerpt, and a link to the agent dashboard.
- Allow agents to click "Claim Ticket" directly from Slack.

---

### 6.5 CRM Sync (HubSpot / Salesforce)
After a conversation is completed, push a contact record and conversation summary to the business's CRM. This is particularly valuable for B2B support teams tracking customer health.

---

## 7. Dashboard & Frontend

### 7.1 Customer-Facing Chat Interface
A polished, embeddable chat widget (see Section 5.7) plus a standalone hosted page at `chat.shopdesksupport.com/[org_slug]`.

- Real-time streaming token display (no loading spinner).
- Message history loaded on open.
- Status indicators: "Morino is typing…", "Connected to human agent".
- File/image upload support.
- CSAT prompt at conversation end.

---

### 7.2 Human Agent Console
A real-time, WebSocket-powered dashboard (see Section 5.1):
- Live ticket queue with priority sorting.
- Full conversation transcript with AI-generated metadata: detected intent, sentiment timeline, customer info.
- Quick-reply templates.
- Internal ticket notes (not visible to customer).
- Handback to AI: agent can return a resolved ticket to the AI for follow-up.

---

### 7.3 Tenant Admin Portal
A settings and analytics portal:
- Knowledge base manager (drag-and-drop document upload with ingestion status).
- Agent configuration panel (persona name, tone, escalation thresholds).
- Team management (invite human agents, assign roles, set schedules).
- Analytics dashboard (see Section 8).
- API key management and webhook configuration.
- Billing and subscription management.

---

## 8. Observability & Analytics

### 8.1 LLM Observability
**Integrate LangSmith (or Arize Phoenix):**
- Trace every chain execution end-to-end (router → worker → final response).
- Track: latency per step, token count, model used, cost per conversation.
- Group by tenant to calculate per-customer LLM costs (critical for profitability analysis and tiered pricing).
- Flag conversations where the RAG retrieval returned low-score results.

---

### 8.2 Product Analytics Dashboard
Key metrics every CEO will ask about on the first demo call:
- **Ticket Deflection Rate:** `(AI-resolved conversations / total conversations) × 100%`.
- **Average First Response Time:** Time from session creation to first AI message.
- **Average Resolution Time:** Time from first message to session close.
- **Escalation Rate:** `(Escalated tickets / total conversations) × 100%`. If this is above 30%, the knowledge base or agent logic needs improvement.
- **CSAT Score:** Rolling 7-day and 30-day average.
- **Top Intent Categories:** A bar chart of what customers are asking about most — drives knowledge base investment decisions.
- **Knowledge Base Coverage:** Which topics are answered confidently (high RAG score) vs. which are missing (low score → frequent escalations).
- **Cost Per Ticket:** Total LLM API cost / number of conversations. Shows ROI vs. a human agent.

---

### 8.3 Application Performance Monitoring
- Integrate **OpenTelemetry** for distributed tracing.
- Export traces and metrics to Grafana + Prometheus or Datadog.
- Alert on: P95 response latency > 5s, error rate > 1%, Pinecone query timeout, Groq rate limit hits.

---

### 8.4 Structured Logging Improvements
**Current:** Structured logging is set up, but log records have no `session_id`, `org_id`, `user_id`, or `request_id` fields, making triage in production nearly impossible.

**Fix:**
- Add a `request_id` middleware that generates a UUID per request and injects it into the logging context.
- Propagate `session_id`, `user_id`, and `org_id` as structured log fields throughout the agent pipeline.
- Ship logs to a centralised log platform (Datadog, Loki + Grafana, or AWS CloudWatch).

---

## 9. Security & Compliance

### 9.1 Role-Based Access Control (RBAC)
**Current:** `UserRole` has only `CUSTOMER` and `AGENT`. There is no enforcement of what each role can access.

**Expand to:**
- `SUPER_ADMIN` — ShopDesk platform operator.
- `ORG_ADMIN` — the business owner/admin (full access to their tenant).
- `SUPPORT_MANAGER` — can view analytics, manage the queue, review AI.
- `SUPPORT_AGENT` — can only view and respond to assigned tickets.
- `CUSTOMER` — can only create sessions and send messages.

Create middleware that checks role requirements on each endpoint. The `GET /queue` endpoint, for example, should only be accessible to `SUPPORT_AGENT` and above — not customers.

---

### 9.2 Audit Logging
For enterprise trust and GDPR compliance:
- Every write operation (ticket status change, user data update, knowledge base upload, role change) must be logged to an `AuditLog` table with: `actor_id`, `action`, `resource_type`, `resource_id`, `old_value`, `new_value`, `timestamp`, `ip_address`.
- Audit logs must be immutable — no UPDATE or DELETE operations on this table.

---

### 9.3 Data Retention Policies
- Add configurable per-tenant data retention policies: "Auto-delete conversations older than 90 days".
- Implement a scheduled Celery task that enforces retention policies.
- Provide a GDPR `DELETE /users/me` endpoint (right to erasure) that hard-deletes all personal data.

---

### 9.4 API Key Authentication for Businesses
In addition to JWT (used for the customer-facing chat), add API key authentication for B2B integrations:
- Businesses authenticate server-to-server using a long-lived API key.
- `POST /apikeys` to generate a key, scoped to specific permissions.
- Store keys hashed (SHA-256), same as passwords.

---

### 9.5 Single Sign-On (SSO)
For enterprise businesses whose teams need to log into the agent dashboard:
- Implement OAuth2 / SAML integration with Google Workspace, Microsoft Azure AD, and Okta.
- Use `python-social-auth` or `authlib` for the OAuth flows.
- Map the business's internal identity to a ShopDesk `User` record with an `org_id`.

---

### 9.6 Input Validation & Prompt Injection Defence
**Current:** The `ChatRequest` schema has a single `content: str` field with no length limit or sanitisation.

**Fix:**
- Add a `max_length=4096` validator on `content`.
- Before passing user input to any LLM, run it through a lightweight prompt injection detector.
- Reject (or sanitise) messages containing known LLM instruction injection patterns (`"Ignore all previous instructions..."`, `"You are now..."`, etc.).

---

## 10. Testing & DevOps

### 10.1 The Test Suite Needs Serious Work
**Current:** The `tests/` folder exists but the tests are mostly stubs or test happy-path unit scenarios in isolation.

**What to add:**
- **Integration tests:** Tests that hit a real test database and verify the full request→response cycle for each API endpoint.
- **RAG quality tests (LLM Eval):** Use `RAGAS` to evaluate retrieval faithfulness and answer relevance. Run in CI to detect if a knowledge base change or prompt change degraded answer quality.
- **Agent behaviour tests:** Parameterised tests with pre-defined queries that must route to specific intents. Regression tests that verify the router does not misclassify obvious cases.
- **Load tests:** Use `Locust` to simulate concurrent chat requests and identify bottlenecks before they appear in production.

---

### 10.2 CI/CD Pipeline
**Current:** No CI/CD. Deployment is manual.

**What to build (GitHub Actions):**
```
On Pull Request:
  1. Lint (ruff, mypy)
  2. Run unit tests
  3. Run integration tests against a test DB
  4. Run RAGAS eval (fail if score drops below threshold)

On Merge to Main:
  5. Build Docker image
  6. Push to ECR / Docker Hub
  7. Deploy to staging (ECS / Cloud Run)
  8. Run smoke tests against staging

On Release Tag:
  9. Blue/green deploy to production
```

---

### 10.3 Infrastructure as Code
Move away from manual Docker Compose:
- **Terraform** for infrastructure (RDS for Postgres, ElastiCache for Redis, ECS for the app, Pinecone managed via API).
- **Docker Compose** retains its place for local development.
- Separate environment configurations: `local`, `staging`, `production`.

---

### 10.4 Secrets Management
**Current:** Secrets are stored in `.env` files (committed `.env.example` exists which is good, but in practice `.env` files often leak).

**Production standard:** Use AWS Secrets Manager or Vault (HashiCorp). Never pass secrets as container environment variables in plain text in production.

---

## 11. Phased Execution Plan

This is the sequence to maximise impact while keeping scope manageable. Each phase produces a deployable, demonstrable product.

---

### Phase 1 — Make It Correct (Fix What's Broken)
*Estimated duration: 2–3 weeks*

The goal is to eliminate the bugs and security issues that would embarrass the project in a code review or cause failures in a demo.

- [ ] Fix the `User.user_id` UUID default bug (Section 2.4)
- [ ] Fix history parsing — stop using string prefix stripping (Section 2.3)
- [ ] Implement proper logout with Redis token blacklist (Section 2.1)
- [ ] Remove PII from LLM context (Section 2.2)
- [ ] Fix user enumeration via auth error messages (Section 2.6)
- [ ] Add RAG similarity score threshold (Section 2.8)
- [ ] Change `EscalationTicket.reason` to `Text` (Section 2.7)
- [ ] Make the Orchestrator LLM client a singleton (Section 2.5)
- [ ] Add input length validation to `ChatRequest` (Section 9.6)
- [ ] Build the password reset flow (Section 5.8)
- [ ] Build email verification (Section 5.9)

---

### Phase 2 — Make It a Real Product (Core Architecture)
*Estimated duration: 6–8 weeks*

The goal is to make the system capable of hosting multiple paying customers.

- [ ] Multi-tenancy: `Organisation` model, `org_id` on all tables, per-tenant Pinecone namespaces (Section 3.1)
- [ ] Full RBAC implementation (Section 9.1)
- [ ] Async SQLAlchemy sessions + async FastAPI routes (Section 3.3)
- [ ] Streaming responses via SSE (Section 3.2)
- [ ] Redis integration for rate limiting + caching (Section 3.4)
- [ ] Knowledge base management API (`/knowledge-base/upload`, delete, sync) (Section 5.3)
- [ ] Agentic write tools: `cancel_order`, `initiate_return` (Section 4.2)
- [ ] LLM fallback chain (Section 4.1)
- [ ] Sentiment analysis + dynamic escalation (Section 4.3)
- [ ] Audit logging (Section 9.2)

---

### Phase 3 — Make It Sellable (Product & UX)
*Estimated duration: 8–10 weeks*

The goal is to have something visually impressive enough to demo to a CEO, and complete enough to charge for.

- [ ] Human Agent Dashboard: real-time WebSocket queue + live takeover (Section 5.1)
- [ ] Tenant Admin Portal: analytics, knowledge base manager, team management (Section 5.2)
- [ ] Embeddable chat widget (Section 5.7)
- [ ] CSAT collection (Section 5.5)
- [ ] Webhook system (Section 5.6)
- [ ] LangSmith integration for LLM observability (Section 8.1)
- [ ] Product analytics dashboard (Section 8.2)
- [ ] WhatsApp integration (Section 6.1)
- [ ] Zendesk integration (Section 6.3)

---

### Phase 4 — Make It Enterprise Grade
*Estimated duration: ongoing*

The goal is to satisfy enterprise procurement checklists and expand TAM.

- [ ] Advanced RAG: re-ranking + hybrid search + contextual chunking + citations (Section 4.4)
- [ ] Multilingual support (Section 4.7)
- [ ] Multimodal image understanding (Section 4.6)
- [ ] Proactive support engine (Section 5.4)
- [ ] SSO (Google, Azure AD, Okta) (Section 9.5)
- [ ] Data retention policies + GDPR right to erasure (Section 9.3)
- [ ] OpenTelemetry + Grafana APM (Section 8.3)
- [ ] Email inbound parsing support (Section 6.2)
- [ ] Slack integration (Section 6.4)
- [ ] CI/CD pipeline + Terraform IaC (Sections 10.2, 10.3)
- [ ] RAGAS-based RAG quality CI gate (Section 10.1)
- [ ] Load testing with Locust (Section 10.1)

---

## What a CEO Cares About

To close this document, here is a translation of the above into the language of a CEO:

| CEO Question | Feature That Answers It |
|---|---|
| "Can it handle my whole support team's volume?" | Async architecture + horizontal scaling (Phase 2) |
| "What's my ROI? How much does it save me?" | Ticket deflection rate + cost-per-ticket analytics dashboard (Phase 3) |
| "Will my competitors see my customer data?" | Multi-tenancy isolation, audit logs, data retention (Phases 2, 4) |
| "Can my team take over when the AI gets it wrong?" | Human agent live takeover dashboard (Phase 3) |
| "Does it work on WhatsApp? That's where my customers are." | WhatsApp integration (Phase 3) |
| "It's too slow. My customers won't wait." | Streaming SSE responses (Phase 2) |
| "Is it secure? We're SOC 2." | RBAC, audit logs, SSO, input validation (Phases 2, 4) |
| "Can I add my own product data to it?" | Knowledge base upload portal + ingestion API (Phase 2) |

---

*Document generated: March 2026. Based on a complete code review of all files in the `shopdesk-support` repository.*
