from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class JobDetails(BaseModel):
    id: int
    title: str
    company: str
    url: str
    description: str
    requirements: List[str]
    nice_to_have: List[str] = []


class TailoredResume(BaseModel):
    """
    Structured output from the LLM, validated before DOCX generation.
    """

    model_config = ConfigDict(extra="forbid")

    summary: str
    skills: List[str]
    experience_bullets: List[str]
    projects_bullets: List[str] = []


class JobRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: JobDetails
    status: str  # "success" | "failed"
    output_resume_path: Optional[str] = None
    error: Optional[str] = None

