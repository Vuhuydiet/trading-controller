# AI Analysis Flow - Crypto Trading Platform

## 📊 Overview Flow Diagram

```
┌─────────────┐
│   Client    │ (Frontend / News Crawler)
└──────┬──────┘
       │ POST /api/v1/analysis/analyze-news
       │ Body: { news_id, news_content, published_at }
       │ Header: Authorization: Bearer <VIP-token>
       ▼
┌──────────────────────────────────────────────────────────┐
│                    API Gateway                            │
│                  (FastAPI Router)                         │
└──────┬───────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│   Authentication & Authorization        │
│   (require_vip_access middleware)       │
├─────────────────────────────────────────┤
│ 1. Decode JWT token                     │
│ 2. Get user tier from token             │
│ 3. Check: tier == VIP?                  │
│    ├─ YES → Continue                    │
│    └─ NO  → 403 Forbidden               │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│        Dependency Injection             │
│        (get_handler factory)            │
├─────────────────────────────────────────┤
│ Initialize components:                  │
│ - sentiment_bot = get_sentiment_analyzer() │
│ - reasoning_bot = get_market_reasoner()    │
│ - repo = SqlModelAnalysisRepo()            │
│ - aligner = NewsPriceAligner()             │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│       AnalyzeNewsHandler.execute()      │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │ Step 1: News-Price Alignment       │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│           ▼                              │
│  ┌────────────────────────────────────┐ │
│  │ NewsPriceAligner.align_data()      │ │
│  ├────────────────────────────────────┤ │
│  │ - Query market module for price    │ │
│  │ - Get BTCUSDT movements around     │ │
│  │   published_at timestamp           │ │
│  │ - Create enriched context:         │ │
│  │   "News: ... + Market: ..."        │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│           ▼                              │
│  ┌────────────────────────────────────┐ │
│  │ Step 2: Parallel AI Analysis       │ │
│  └────────┬───────────────────────────┘ │
│           │                              │
│     ┌─────┴─────┐                       │
│     │           │                       │
│     ▼           ▼                       │
│ ┌──────┐   ┌──────────┐                │
│ │Task 1│   │ Task 2   │                │
│ └──┬───┘   └────┬─────┘                │
│    │            │                       │
│    │            │                       │
└────┼────────────┼───────────────────────┘
     │            │
     │            │
     ▼            ▼
┌─────────────┐  ┌──────────────────────┐
│ Sentiment   │  │ Reasoning            │
│ Analysis    │  │ Analysis             │
└─────────────┘  └──────────────────────┘
```

---

## 🔄 Detailed Step-by-Step Flow

### **Step 0: Client Request**

```http
POST /api/v1/analysis/analyze-news
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "news_id": "reuters_20260111_001",
  "news_content": "US Federal Reserve approves new Bitcoin ETF regulations",
  "published_at": "2026-01-11T14:30:00Z"
}
```

---

### **Step 1: Authentication Check** ⚡

**File**: `app/modules/analysis/features/analyze_news/router.py:41-56`

```python
def require_vip_access(user: UserDTO = Depends(get_current_user_dto)):
    # 1.1: Decode JWT token from Authorization header
    # 1.2: Extract user_id, tier from token payload
    # 1.3: Check tier == "VIP"
    if user.tier != UserTier.VIP:
        raise HTTPException(403, detail={
            "error": "AI Analysis requires VIP subscription",
            "current_tier": user.tier  # e.g., "FREE"
        })
    return user
```

**Possible Outcomes**:
- ✅ VIP user → Continue to Step 2
- ❌ FREE user → HTTP 403 Forbidden
- ❌ No token → HTTP 401 Unauthorized

---

### **Step 2: Model Factory (Config-Based Loading)** 🏭

**File**: `app/shared/infrastructure/ai/model_factory.py`

```python
# Read from .env configuration
AI_SENTIMENT_MODEL = "finbert"
AI_REASONING_PROVIDER = "ollama"
AI_REASONING_MODEL = "llama3.2"

# Load sentiment analyzer
sentiment_bot = get_sentiment_analyzer()
  └─> if AI_SENTIMENT_MODEL == "finbert":
        return FinBertAdapter()
      # Future: elif == "openai": return OpenAISentimentAdapter()

# Load reasoning model
reasoning_bot = get_market_reasoner()
  └─> if AI_REASONING_PROVIDER == "ollama":
        return OllamaLlamaAdapter(model_name="llama3.2")
      # Future: elif == "gemini": return GeminiAdapter()
```

**Loaded Components**:
- ✅ FinBertAdapter (for sentiment)
- ✅ OllamaLlamaAdapter (for reasoning)
- ✅ SqlModelAnalysisRepo (for saving results)
- ✅ NewsPriceAligner (for data preparation)

---

### **Step 3: News-Price Alignment** 🔗

**File**: `app/modules/analysis/domain/services.py`

```python
aligned_context = await aligner.align_data_for_ai(
    news_content="US Federal Reserve approves new Bitcoin ETF...",
    published_at="2026-01-11T14:30:00Z"
)
```

**Internal Process**:
```python
# 3.1: Call Market module API
market_context = await get_price_movements(
    symbol="BTCUSDT",
    target_time="2026-01-11T14:30:00Z"
)
# Returns: "BTC/USDT: +3.5% in 24h, Volume: 45B USD"

# 3.2: Combine news + market data
aligned_context = f"""
--- NEWS CONTENT ---
"US Federal Reserve approves new Bitcoin ETF regulations"
Published at: 2026-01-11 14:30:00

--- MARKET REACTION ---
BTC/USDT: +3.5% in 24h
Volume: 45B USD
"""
```

**Output**: Enriched context string combining news + market data

---

### **Step 4: Parallel AI Analysis** ⚡⚡

**File**: `app/modules/analysis/features/analyze_news/handler.py:26-30`

```python
# Create two async tasks (NOT executed yet)
sentiment_task = sentiment_bot.analyze_sentiment(request.news_content)
reasoning_task = reasoning_bot.explain_market_trend(news=aligned_context)

# Execute both in parallel
sentiment_result, reasoning_result = await asyncio.gather(
    sentiment_task,
    reasoning_task
)
```

---

#### **Branch A: Sentiment Analysis** 🎭

**File**: `app/shared/infrastructure/ai/sentiment_adapter.py`

```python
class FinBertAdapter:
    async def analyze_sentiment(text: str) -> SentimentResult:
        # A.1: Truncate text to 512 chars (BERT limit)
        truncated = text[:512]

        # A.2: Run FinBERT model
        result = self.pipe(truncated)
        # Returns: [{'label': 'positive', 'score': 0.92}]

        # A.3: Convert to Pydantic model
        return SentimentResult(
            label='positive',
            score=0.92
        )
```

**GPU/CPU Selection**:
```python
device = 0 if torch.cuda.is_available() else -1
# 0 = GPU (CUDA), -1 = CPU
```

**Output**:
```python
SentimentResult(
    label="positive",
    score=0.92
)
```

---

#### **Branch B: Trend Reasoning** 🔮

**File**: `app/shared/infrastructure/ai/reasoning_adapter.py`

```python
class OllamaLlamaAdapter:
    async def explain_market_trend(news: str) -> ReasoningResult:
        # B.1: Create prompt for LLM
        prompt = f"""
        You are a crypto market expert. Analyze:
        {aligned_context}

        Task: Predict trend (UP/DOWN/NEUTRAL) and explain.
        Return JSON: {{"trend": "UP", "reasoning": "..."}}
        """

        # B.2: Call Ollama API
        response = ollama.chat(
            model="llama3.2",
            messages=[{'role': 'user', 'content': prompt}]
        )
        # Response: '{"trend": "UP", "reasoning": "Positive..."}'

        # B.3: Parse JSON from response
        parsed = json.loads(response['message']['content'])

        # B.4: Convert to Pydantic model
        return ReasoningResult(
            trend="UP",
            reasoning="Positive regulatory news typically drives..."
        )
```

**Error Handling**:
```python
except Exception as e:
    return ReasoningResult(
        trend="NEUTRAL",
        reasoning=f"AI Analysis Failed: {str(e)}"
    )
```

**Output**:
```python
ReasoningResult(
    trend="UP",
    reasoning="Positive regulatory news typically drives institutional adoption"
)
```

---

### **Step 5: Save to Database** 💾

**File**: `app/modules/analysis/infrastructure/repository.py`

```python
await repo.save_analysis_result(
    news_id="reuters_20260111_001",
    sentiment="positive",
    confidence=0.92,
    trend="UP",
    reasoning="Positive regulatory news typically drives..."
)
```

**Database Table**: `analysis_results`

| Column      | Value                                    |
|-------------|------------------------------------------|
| news_id     | reuters_20260111_001                     |
| sentiment   | positive                                 |
| confidence  | 0.92                                     |
| trend       | UP                                       |
| reasoning   | Positive regulatory news typically...   |
| created_at  | 2026-01-11 14:35:22                     |

---

### **Step 6: Return Response** 📤

**File**: `app/modules/analysis/features/analyze_news/handler.py:42-47`

```python
return AnalyzeNewsResponse(
    sentiment="positive",
    confidence=0.92,
    trend="UP",
    reasoning="Positive regulatory news typically drives institutional adoption"
)
```

**HTTP Response**:
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "sentiment": "positive",
  "confidence": 0.92,
  "trend": "UP",
  "reasoning": "Positive regulatory news typically drives institutional adoption"
}
```

---

## ⏱️ Timeline Diagram

```
T+0ms    Client sends request
         │
T+10ms   ├─> JWT validation
         │
T+15ms   ├─> Load AI models from factory
         │
T+20ms   ├─> News-Price alignment (query market data)
         │
T+50ms   ├─> Start parallel AI analysis
         │   │
         │   ├─── Task A: FinBERT sentiment
         │   │    (500ms - 2000ms depending on GPU/CPU)
         │   │
         │   └─── Task B: Llama reasoning
         │        (2000ms - 5000ms for Ollama)
         │
T+2050ms │   Both tasks complete (using max time)
         │
T+2060ms ├─> Save to database
         │
T+2070ms └─> Return response to client

Total: ~2 seconds (with GPU) or ~7 seconds (CPU only)
```

---

## 🔀 Alternative Flows

### **Flow 1: Non-VIP User Access**

```
Client Request
    ├─> JWT validation ✅
    ├─> Check tier
    │   └─> tier = "FREE" ❌
    └─> HTTP 403 Forbidden

Response:
{
  "detail": {
    "error": "AI Analysis requires VIP subscription",
    "current_tier": "FREE",
    "required_tier": "VIP"
  }
}
```

---

### **Flow 2: Model Switching via Config**

**Scenario**: User changes `.env` to use GPT-4 instead of Llama

```bash
# .env
AI_REASONING_PROVIDER=openai
AI_REASONING_MODEL=gpt-4
OPENAI_API_KEY=sk-proj-xxxxx
```

**New Flow**:
```
Step 2: Model Factory
    └─> if AI_REASONING_PROVIDER == "openai":
          return OpenAIReasoningAdapter(model="gpt-4")

Step 4B: Reasoning with GPT-4
    └─> Call OpenAI API instead of Ollama
        (faster response, cloud-based)
```

**No code changes needed!** Just restart server.

---

### **Flow 3: AI Model Failure**

```
Step 4B: Llama Reasoning
    ├─> ollama.chat() throws exception
    │   (e.g., Ollama server not running)
    │
    └─> Catch exception
        └─> Return fallback:
            ReasoningResult(
                trend="NEUTRAL",
                reasoning="AI Analysis Failed: Connection refused"
            )
```

**Response still returns 200 OK** (graceful degradation):
```json
{
  "sentiment": "positive",
  "confidence": 0.92,
  "trend": "NEUTRAL",
  "reasoning": "AI Analysis Failed: Connection refused"
}
```

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────────────┐
│          Presentation Layer                     │
│  (FastAPI Router - analyze_news endpoint)       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         Application Layer                       │
│  (AnalyzeNewsHandler - orchestration)           │
└─────────────────┬───────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼─────┐ ┌──▼──────┐ ┌──▼──────────┐
│  Domain   │ │ Domain  │ │   Domain    │
│  Service  │ │  Ports  │ │  Entities   │
│ (Aligner) │ │(Interf.)│ │(AnalysisRes)│
└───────────┘ └────┬────┘ └─────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│       Infrastructure Layer                      │
├─────────────────────────────────────────────────┤
│ - FinBertAdapter (implements SentimentPort)     │
│ - OllamaLlamaAdapter (implements ReasonerPort)  │
│ - SqlModelAnalysisRepo (implements RepoPort)    │
│ - Model Factory (config-based loading)          │
└─────────────────────────────────────────────────┘
```

---

## 📦 Component Responsibilities

| Component               | Responsibility                          |
|-------------------------|-----------------------------------------|
| **Router**              | HTTP request handling, auth check       |
| **Handler**             | Orchestrate business logic flow         |
| **NewsPriceAligner**    | Enrich news with market data            |
| **FinBertAdapter**      | Sentiment analysis implementation       |
| **OllamaLlamaAdapter**  | Trend reasoning implementation          |
| **AnalysisRepo**        | Persist results to database             |
| **Model Factory**       | Config-based model instantiation        |
| **Ports (Interfaces)**  | Define contracts for implementations    |

---

## 🔧 Configuration Impact

```
.env File Changes → Behavior Changes
─────────────────────────────────────
AI_SENTIMENT_MODEL=finbert
  → Uses FinBERT (local, free, fast)

AI_SENTIMENT_MODEL=openai
  → Uses GPT-4 (cloud, paid, accurate)

AI_REASONING_PROVIDER=ollama
  → Uses Llama 3.2 (local, privacy-first)

AI_REASONING_PROVIDER=gemini
  → Uses Gemini Pro (cloud, Google)

AI_REASONING_MODEL=llama3.2
  → Specific model version for Ollama

AI_REASONING_MODEL=gpt-4-turbo
  → Use GPT-4 Turbo if provider=openai
```

---

## 🎯 Summary

**Input**: News content + metadata
**Process**: Auth check → Data alignment → Parallel AI (Sentiment + Reasoning) → Save → Return
**Output**: Sentiment label + confidence + trend + reasoning

**Key Features**:
- ✅ VIP-only access control
- ✅ Parallel processing (sentiment + reasoning)
- ✅ Config-based model switching
- ✅ Type-safe with Pydantic models
- ✅ Graceful error handling
- ✅ Database persistence

**Performance**: ~2 seconds (GPU) or ~7 seconds (CPU) per analysis
