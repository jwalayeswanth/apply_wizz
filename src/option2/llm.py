from __future__ import annotations

import json
from typing import Tuple

from openai import OpenAI

from .config import Settings
from .types import JobDetails, TailoredResume


def _fallback_tailoring(job: JobDetails) -> TailoredResume:
    focus = (job.requirements + job.nice_to_have)[:10]
    # Conservative fallback: we only restate job focus areas, not claim new facts.
    focus_str = ", ".join(focus[:6]) if focus else job.title
    return TailoredResume(
        summary=f"Tailored for the {job.title} role. Focus areas: {focus_str}.",
        skills=focus[:12] if focus else [],
        experience_bullets=[
            f"Resume alignment to role requirements (verify details in your resume): {r}"
            for r in job.requirements[:4]
        ],
        projects_bullets=[
            f"Potential projects to emphasize (based on job focus; verify in your resume): {n}"
            for n in job.nice_to_have[:3]
        ],
    )


def _build_prompt(job: JobDetails, base_resume_text: str, error_hint: str | None) -> list[dict]:
    system = (
        "You tailor resumes for job postings. "
        "You MUST output a single JSON object that matches the required schema exactly. "
        "Use only information from the provided base resume text; do not invent metrics, employers, or projects. "
        "If unsure, write conservative, verification-oriented phrasing."
    )

    schema_hint = (
        "Required JSON schema keys:\n"
        "- summary: string\n"
        "- skills: string[] (8-15 items)\n"
        "- experience_bullets: string[] (4-7 items)\n"
        "- projects_bullets: string[] (0-5 items)\n"
        "No additional keys."
    )

    user_parts = [
        "Tailor this resume for the following job.",
        "",
        f"Job Title: {job.title}",
        f"Company: {job.company}",
        f"URL: {job.url}",
        "",
        "Job Description:",
        job.description,
        "",
        f"Requirements: {json.dumps(job.requirements)}",
        f"Nice to have: {json.dumps(job.nice_to_have)}",
        "",
        "Base Resume Text (use as the only factual source):",
        base_resume_text,
        "",
        schema_hint,
        "Return ONLY the JSON object. No markdown.",
    ]
    if error_hint:
        user_parts.append("")
        user_parts.append("Previous output failed validation/parsing. Fix it:")
        user_parts.append(error_hint)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": "\n".join(user_parts)},
    ]


def tailor_resume(settings: Settings, job: JobDetails, base_resume_text: str) -> Tuple[TailoredResume, str]:
    """
    Returns (tailored_resume, status_detail).
    status_detail explains whether it used the LLM or a fallback.
    """

    client = OpenAI(api_key=settings.openai_api_key)

    # Retry once if parsing/validation fails.
    for attempt in (0, 1):
        error_hint = None
        if attempt == 1:
            # This hint is generic; we fill in parsing/validation details once we have them.
            error_hint = "Return valid JSON matching the schema keys exactly. Ensure types are correct."

        prompt = _build_prompt(job, base_resume_text, error_hint=error_hint)
        try:
            resp = client.chat.completions.create(
                model=settings.openai_model,
                messages=prompt,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            content = resp.choices[0].message.content or ""
            data = json.loads(content)
            tailored = TailoredResume.model_validate(data)
            return tailored, f"llm_json_valid_attempt_{attempt+1}"
        except Exception as e:
            last_error = e
            if attempt == 0:
                # Retry with more precise error context.
                continue
            break

    # Fallback if we still couldn't validate.
    return _fallback_tailoring(job), f"fallback_after_error:{type(last_error).__name__}"

