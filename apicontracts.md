# API Contracts & Interface Definitions: Maxume

## 1. Local Ollama Integration Contract

Maxume interacts with the local **Ollama** server over localhost using standardized JSON payloads.

*   **Default Endpoint**: `POST http://localhost:11434/api/generate`
*   **Protocol**: JSON
*   **Model**: `qwen2.5:7b-instruct` — matches the model pulled in `envsetup.md` (`ollama pull qwen2.5:7b-instruct`) and the `OLLAMA_MODEL_NAME` value in `.env`. Keep these three references in sync if the default model ever changes.

### Input Payload Schema
Caps `num_ctx` to **2048** and enables Flash Attention, keeping the model within the ~5.2GB VRAM budget on an RTX 3060 Laptop.

```json
{
  "model": "qwen2.5:7b-instruct",
  "prompt": "Extract the key professional technical achievements from the following project file. Structure your output into 4 concise bullet points.\n\nProject Logs:\n[INSERT RAW LOGS]",
  "stream": false,
  "options": {
    "num_ctx": 2048,
    "temperature": 0.2,
    "top_p": 0.9,
    "num_predict": 512
  }
}
```

### Expected JSON Response
```json
{
  "model": "qwen2.5:7b-instruct",
  "created_at": "2026-08-14T12:00:00.123456Z",
  "response": "- Engineered high-performance key-value database using Go, achieving sub-millisecond latencies.\n- Optimized storage overhead by 30% through targeted binary serialization of memory blocks.",
  "done": true,
  "context": [124, 3948, 882],
  "total_duration": 1420194800,
  "load_duration": 10029300,
  "prompt_eval_count": 256,
  "prompt_eval_duration": 140294000,
  "eval_count": 82,
  "eval_duration": 1210400000
}
```

---

## 2. Cloud-Based Gemini Developer API (AI Studio)

Maxume uses Google's free **Gemini 2.5 Flash-Lite** endpoint (1,000 requests/day) for heavy-context jobs: OCR on screenshot JDs, project reranking, and company-signal summarization.

*   **Endpoint**: `POST https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={API_KEY}`

### OCR Request Payload (Multimodal Base64 Image Processing)
```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "Identify and extract the clean text from this job description screenshot. Output the role title, company name, and the core technical requirements."
        },
        {
          "inlineData": {
            "mimeType": "image/jpeg",
            "data": "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP...[Compressed Image Base64]"
          }
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.1,
    "maxOutputTokens": 2048
  }
}
```

---

## 3. High-Speed Groq Cloud API

Maxume routes cover letter, referral, and email generation through **Groq** (`llama-3.3-70b-specdec`, 14,400 free requests/day).

*   **Endpoint**: `POST https://api.groq.com/openai/v1/chat/completions`

### Input Payload Schema
The system prompt must include the grounding constraint from the company research brief — either the cited signals, or an explicit instruction to avoid company-specific factual claims when `research_status` is `NO_SIGNALS_FOUND`.

```json
{
  "model": "llama-3.3-70b-specdec",
  "messages": [
    {
      "role": "system",
      "content": "You are an expert technical resume coach and career counselor. Generate a persuasive, professional cover letter. You may only reference the company facts listed under RESEARCH_BRIEF below; if RESEARCH_BRIEF is empty, write a strong letter based on the role and candidate background alone and do not invent or imply any company-specific news, launches, or milestones."
    },
    {
      "role": "user",
      "content": "Create a 300-word cover letter for a Software Engineer role at [COMPANY]. My resume highlights: [INSERT KEY BULLETS].\n\nRESEARCH_BRIEF:\n[INSERT CITED SIGNALS, OR \"NO_SIGNALS_FOUND\"]"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

---

## 4. Google Custom Search Engine (CSE) — Employee Lookup

To bypass LinkedIn cookie limitations and surface company employees with zero ban risk, Maxume uses Google's Custom Search JSON API.

*   **Endpoint**: `GET https://customsearch.googleapis.com/customsearch/v1`

### Query Parameters Schema
```
GET /customsearch/v1?key={API_KEY}&cx={CSE_ID}&q=site:linkedin.com/in/+"Amazon"+AND+("Software+Engineer"+OR+"SDE"+OR+"HR")
```

### JSON Response Schema
```json
{
  "kind": "customsearch#search",
  "queries": {
    "request": [
      {
        "title": "Google Custom Search - site:linkedin.com/in/ \"Amazon\" AND (\"Software Engineer\")",
        "totalResults": "184000",
        "searchTerms": "site:linkedin.com/in/ \"Amazon\" AND (\"Software Engineer\")",
        "count": 3,
        "startIndex": 1
      }
    ]
  },
  "items": [
    {
      "kind": "customsearch#result",
      "title": "Jane Doe - Senior Software Engineer - Amazon | LinkedIn",
      "htmlTitle": "Jane Doe - Senior <b>Software Engineer</b> - <b>Amazon</b> | LinkedIn",
      "link": "https://www.linkedin.com/in/janedoe",
      "displayLink": "www.linkedin.com",
      "snippet": "View Jane Doe's profile on LinkedIn. Senior Software Engineer at Amazon. Technical Expertise in AWS, Distributed Systems, and High-Performance APIs.",
      "pagemap": {
        "metatags": [
          { "profile:first_name": "Jane", "profile:last_name": "Doe" }
        ]
      }
    }
  ]
}
```
The Python sidecar extracts the name from `title`, the tagline from `snippet`, and the direct profile link from `link` to render contact cards in the React UI.

---

## 5. Company Signal Research Contract (New)

See `companyresearch.md` for the full pipeline design and hallucination guard. This section defines the concrete schema.

### 5a. Discovery Query (Google CSE, News-Oriented)
```
GET /customsearch/v1?key={API_KEY}&cx={CSE_ID}&q="[COMPANY_NAME]"+(news+OR+"product+launch"+OR+funding+OR+"raises")&sort=date&num=5
```

### 5b. Internal Function Contract — `research_company()`
Input:
```json
{
  "company_name": "Acme Robotics",
  "company_url": "https://acme.example.com",
  "recency_days": 90,
  "max_signals": 5
}
```

Output — signal(s) found:
```json
{
  "status": "FOUND",
  "signals": [
    {
      "signal_type": "product_launch",
      "headline": "Acme Robotics unveils warehouse-picking arm v3",
      "source_url": "https://acme.example.com/blog/warehouse-arm-v3",
      "source_tier": 1,
      "published_at": "2026-07-02",
      "guard_check_passed": true
    }
  ]
}
```

Output — nothing qualifying found (the required, non-error fallback state):
```json
{
  "status": "NO_SIGNALS_FOUND",
  "signals": []
}
```

### 5c. Gemini Grounded-Summarization Prompt (Stage C)
```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "You will be given raw search snippets about a company, each with its source URL and date. Summarize ONLY what is stated in these snippets into up to 3 short, factual bullet points, each ending with its source URL in parentheses. Do not add outside knowledge, do not infer unstated facts, and do not resolve ambiguity by guessing. If the snippets do not support any usable, specific claim, respond with exactly: NO_SIGNALS_FOUND\n\nSNIPPETS:\n[INSERT RAW SNIPPETS WITH SOURCE + DATE]"
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.0,
    "maxOutputTokens": 512
  }
}
```
`temperature: 0.0` is intentional here — this is the one call in the whole pipeline where creativity is actively undesirable.

### 5d. Post-Hoc Containment Check (Stage D, Deterministic — Not an API Call)
Pseudocode, implemented in `company_research.py`:
```python
def passes_containment_check(summary_bullet: str, source_snippets: list[str]) -> bool:
    # Extract key entities/numbers from the bullet (simple noun-phrase / digit extraction)
    # Confirm each appears verbatim (case-insensitive) in at least one source snippet
    # Return False on any miss -> caller marks guard_check_passed = False and drops the signal
    ...
```
