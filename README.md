# Option 2 — AI Resume Tailoring Agent

This solution implements **Option 2**: it loads job postings + requirements, loads a base candidate resume, uses an LLM to tailor the resume per job, generates a tailored `.docx`, and emails one attachment per job.

## Why this option
- Demonstrates a multi-step, agentic workflow (data ingestion → LLM tailoring → document generation → per-job delivery).
- Validates structured LLM output (so generation is deterministic and failures are recoverable).
- Shows resilient orchestration: a failure for one job does not stop the rest.

## What it does (end-to-end)
1. Read `inputs/option2_job_links.xlsx` and `inputs/option2_jobs.json`, join by `#` / `id`.
2. Extract plain text from `inputs/candidate_resume.docx` once.
3. For each of the 5 jobs:
   - Call the LLM to produce tailored resume content (JSON validated via `pydantic`).
   - Generate `outputs/resumes/resume_<id>_<job_title>.docx`.
   - Email the tailored resume as an attachment (or write a `.eml` draft in `DRY_RUN` mode).
4. Write `outputs/run_report.json` with per-job success/failure + error details.

## Setup

### 1. Install dependencies
```powershell
python -m pip install -r requirements.txt
```

### 2. Configure environment variables
Copy `.env.example` to `.env` and fill in the values:
```powershell
Copy-Item .env.example .env
```

At minimum you need:
- `OPENAI_API_KEY`
- SMTP settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_TO`)

For local testing, you can set `DRY_RUN=true` to avoid sending emails.

### 3. Run the agent
```powershell
python -m src.option2.main --data-dir inputs --out-dir outputs --dry-run
```

After it finishes, check:
- `outputs/resumes/` for the tailored resume `.docx` files
- `outputs/emails/` for `.eml` drafts (when `DRY_RUN` is enabled)
- `outputs/run_report.json` for a per-job execution report

## Implementation notes / design decisions
- **Tailoring prompt**: the prompt instructs the model to use *only* the provided base resume text and not invent new facts.
- **Structured output**: the LLM is asked to return strict JSON; we validate it with `pydantic`. If JSON/parsing fails, we retry once and then fall back to a conservative, requirement-focused template.
- **Resilience**: each job is wrapped in a `try/except`; the agent continues processing remaining jobs and records stack traces in `run_report.json`.
- **Email delivery**: uses SMTP (configured via `.env`). In `DRY_RUN`, the agent writes RFC822 `.eml` drafts with the attachment, which is convenient for demos.

## Assumptions
- `candidate_resume.docx` is the base resume used for all roles.
- The Excel column headers match the spec exactly (`#`, `Job Title`, `Company`, `URL`, `Resume Path`).
- SMTP credentials are available if you want real emails; otherwise set `DRY_RUN=true`.
