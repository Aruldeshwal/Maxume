# API Data Contracts & Endpoint Specifications

## Base URL
`http://127.0.0.1:8000`

---

## 1. Project Management Endpoints

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
    "summary_markdown": "# EzNotes\n**Live Demo**: https://eznotes.onrender.com\n...",
    "tech_stack": "TypeScript, Next.js, React",
    "language": "TypeScript",
    "live_demo_url": "https://eznotes.onrender.com",
    "is_hidden": 0,
    "last_commit_hash": "a1b2c3d4"
  }
]
```

### `POST /api/github/sync`
Syncs all public GitHub repositories for the configured username.
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
  "total_synced": 12,
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
Processes job description text and/or screenshots, reranks top candidate projects, compiles single-page DOCX resume, performs company research, and generates referral outreach drafts.
* **Request**:
```json
{
  "company_name": "Google",
  "role_title": "Software Engineer",
  "company_url": "https://about.google",
  "jd_text": "Looking for a full stack engineer with React, Next.js, and MongoDB experience...",
  "jd_image_base64": "data:image/png;base64,iVBORw0KGgo...",
  "jd_images_base64": ["data:image/png;base64,...", "..."],
  "template_path": "Master_Resume.docx",
  "output_dir": "./output"
}
```
* **Response**:
```json
{
  "status": "ok",
  "application_id": 42,
  "output_folder": "C:/Users/.../output/google",
  "resume_path": "C:/Users/.../output/google/google_Resume.docx",
  "cover_letter_path": "C:/Users/.../output/google/google_CoverLetter.txt",
  "email_path": "C:/Users/.../output/google/google_Email.txt",
  "cover_letter": "Dear Hiring Team at Google...",
  "outreach_email": "Subject: Application for Software Engineer...",
  "personalization_status": "Personalized",
  "research_brief": {
    "status": "FOUND",
    "signals": [
      {
        "signal_type": "product_launch",
        "headline": "Google launches new AI features for developer ecosystem",
        "source_url": "https://news.google.com/...",
        "source_tier": 2,
        "guard_check_passed": true
      }
    ]
  },
  "networking_contacts": [
    {
      "id": 101,
      "employee_name": "Google Senior Engineer / Tech Lead",
      "employee_tagline": "Senior Software Engineer • Distributed Systems at Google",
      "profile_url": "https://www.linkedin.com/search/results/people/?keywords=Google%20Software%20Engineer",
      "referral_message_draft": "Hi Google Senior Engineer / Tech Lead, I came across your work...",
      "referral_status": "Not Contacted"
    }
  ],
  "ranked_projects": [...]
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
  "folder_path": "C:/Users/.../output/google"
}
```
* **Response**:
```json
{
  "status": "ok",
  "opened_path": "C:/Users/.../output/google"
}
```
