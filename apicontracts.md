# API Data Contracts & Endpoint Specifications

## Base URL
`http://127.0.0.1:8000`

---

## 1. Project Management Endpoints

### `GET /api/quotas`
Returns real-time daily usage quotas and limits for zero-cost cloud APIs.
* **Response**:
```json
{
  "gemini": {
    "used": 4,
    "total": 1000
  },
  "groq": {
    "used": 7,
    "total": 14400
  }
}
```

### `GET /api/projects`
Returns all indexed local and GitHub repositories.
* **Query Parameters**:
  * `include_hidden` (boolean, optional, default: `true`)
* **Response**:
```json
[
  {
    "id": 1,
    "directory_name": "EzNotes",
    "summary_markdown": "# EzNotes\n**Live Demo**: https://eznotes-pits.onrender.com/\n...",
    "tech_stack": "Next.js, TypeScript, Node.js, PostgreSQL, Clerk",
    "timeline": "2024 – Present",
    "live_demo_url": "https://eznotes-pits.onrender.com/",
    "is_hidden": 0,
    "bullets": [
      "Architected a highly scalable Next.js application supporting 1M+ concurrent readers by decoupling Edge read path from PostgreSQL database, achieving 99.9% uptime and reducing P95 API latency by 42%",
      "Engineered secure authentication with Clerk, eliminating race conditions via atomic database transactions and OAuth2/JWT with granular RBAC, ensuring 100% data integrity"
    ],
    "last_commit_hash": "2026-08-17"
  }
]
```

### `POST /api/github/sync`
Syncs all public GitHub repositories for the configured username using FAANG Principal Architect AI bullet synthesis.
* **Request**:
```json
{
  "username": "Aruldeshwal"
}
```
* **Response**:
```json
{
  "status": "ok",
  "username": "Aruldeshwal",
  "total_synced": 13,
  "projects": [...]
}
```

### `POST /api/projects/{id}/visibility`
Toggles a project's visibility on compiled resumes.
* **Response**:
```json
{
  "status": "ok",
  "project_id": 1,
  "is_hidden": 1
}
```

### `PUT /api/projects/{id}`
Updates a project's custom tech stack, timeline, live demo URL, or bullets in SQLite SSOT.
* **Request**:
```json
{
  "tech_stack": "Tauri v2, React, TypeScript, FastAPI, Python 3.13, SQLite, Tailwind CSS",
  "timeline": "Oct 2024 – Dec 2024",
  "live_demo_url": "https://example.com",
  "bullets": [
    "Accomplished [X] as measured by [Y], by doing [Z]"
  ]
}
```
* **Response**:
```json
{
  "status": "ok",
  "project_id": 1
}
```

### `DELETE /api/projects/{id}`
Permanently deletes a project from the SQLite database.
* **Response**:
```json
{
  "status": "ok",
  "deleted_id": 1
}
```

---

## 2. Optimization & Application Endpoints

### `POST /api/optimize`
Processes job description text and/or screenshots, reranks top candidate projects, compiles single-page DOCX resume, performs company research, executes real employee discovery, generates Hunter.io-style predicted emails, and creates personalized referral pitches.
* **Request**:
```json
{
  "company_name": "Meritshot",
  "role_title": "Software Engineer",
  "company_url": "https://meritshot.com/careers",
  "company_domain": "@meritshot.com",
  "jd_raw_text": "Looking for a full stack engineer with React, Next.js, and MongoDB experience...",
  "screenshots_base64": ["data:image/png;base64,..."],
  "personalization_enabled": true,
  "pitch_style": "deep_dive"
}
```
* **Response**:
```json
{
  "status": "ok",
  "application_id": 42,
  "output_folder": "C:/Users/aruld/OneDrive/Desktop/Job-Content/Meritshot",
  "resume_path": "C:/Users/aruld/OneDrive/Desktop/Job-Content/Meritshot/Meritshot_Resume.docx",
  "cover_letter_path": "C:/Users/aruld/OneDrive/Desktop/Job-Content/Meritshot/Meritshot_CoverLetter.txt",
  "email_path": "C:/Users/aruld/OneDrive/Desktop/Job-Content/Meritshot/Meritshot_Email.txt",
  "cover_letter": "Hi team at Meritshot, I’ve been following how Meritshot is scaling...",
  "outreach_email": "Subject: Full-Stack Engineer / Metro-Connect project -> Meritshot...",
  "pitch_style": "deep_dive",
  "personalization_status": "Personalized",
  "research_brief": {
    "status": "FOUND",
    "company_name": "Meritshot",
    "company_summary": "AI-driven professional coaching, executive upskilling, and tech career placement ecosystem.",
    "industry_domain": "EdTech & Career Intelligence",
    "technical_priorities": [
      "Real-Time Concurrency & WebSocket State Synchronization",
      "Atomic Database Integrity & Distributed Transactions",
      "Responsive Client-Side UI & Complex State Management"
    ],
    "signals": [
      {
        "signal_type": "product_launch",
        "headline": "Meritshot launches new learning ecosystem",
        "source_url": "https://meritshot.com/...",
        "source_tier": 1,
        "guard_check_passed": true
      }
    ]
  },
  "networking_contacts": [
    {
      "id": 101,
      "employee_name": "Roshan Sharma",
      "employee_tagline": "[👑 Decision Maker] Founder & CEO @ Meritshot",
      "archetype": "👑 Decision Maker",
      "profile_url": "https://in.linkedin.com/in/rroshansharma",
      "domain": "meritshot.com",
      "mx_provider": "Zoho Mail",
      "deliverability_confidence": "90% Deliverability Confirmed",
      "email_primary": "roshan.sharma@meritshot.com",
      "email_alternatives": ["roshan@meritshot.com", "rsharma@meritshot.com"],
      "google_dork_url": "https://www.google.com/search?q=%22Roshan+Sharma%22+%22Meritshot%22",
      "github_search_url": "https://github.com/search?q=Roshan+Sharma&type=users",
      "twitter_search_url": "https://twitter.com/search?q=Roshan+Sharma+Meritshot&f=user",
      "referral_message_draft": "Hi Roshan, built full-stack & AI systems matching your team's stack. Applied for Full Stack Developer at Meritshot & would love to connect!",
      "character_count": 139,
      "referral_status": "Not Contacted"
    }
  ],
  "ranked_projects": [...]
}
```

### `POST /api/employees/lookup`
Direct on-demand real employee lookup and Hunter.io email synthesizer.
* **Request**:
```json
{
  "company_name": "Meritshot",
  "company_url": "https://meritshot.com",
  "company_domain": "@meritshot.com",
  "num_results": 4
}
```
* **Response**:
```json
{
  "status": "ok",
  "contacts": [
    {
      "employee_name": "Roshan Sharma",
      "employee_tagline": "Founder & CEO at Meritshot",
      "profile_url": "https://in.linkedin.com/in/rroshansharma",
      "company_domain": "meritshot.com",
      "mx_status": true,
      "mx_provider": "Zoho Mail",
      "email_primary": "roshan.sharma@meritshot.com",
      "email_alternatives": ["roshan@meritshot.com", "rsharma@meritshot.com"],
      "google_dork_url": "https://www.google.com/search?q=%22Roshan+Sharma%22+%28%22%40meritshot.com%22+OR+email%29",
      "github_search_url": "https://github.com/search?q=Roshan+Sharma+type%3Ausers",
      "twitter_search_url": "https://x.com/search?q=%22Roshan+Sharma%22+%22Meritshot%22",
      "referral_status": "Not Contacted"
    }
  ]
}
```

---

## 3. System & File Utility Endpoints

### `GET /api/ollama/status`
Checks local Ollama service availability and active model.
* **Response**:
```json
{
  "online": true,
  "model": "qwen2.5:7b-instruct",
  "vram": "4.8GB / 5.2GB"
}
```

### `POST /api/open-folder`
Opens the target application output folder or Word document directly in Windows Explorer.
* **Request**:
```json
{
  "path": "C:/Users/aruld/OneDrive/Desktop/Job-Content/Meritshot/Meritshot_Resume.docx"
}
```
* **Response**:
```json
{
  "status": "ok"
}
```
