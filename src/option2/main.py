from __future__ import annotations

import argparse
import json
import os
import traceback
from pathlib import Path

from dotenv import load_dotenv

from .config import load_settings
from .doc_generator import generate_tailored_docx
from .emailer import send_tailored_resume_email
from .job_loader import load_jobs
from .llm import tailor_resume
from .resume_extractor import load_base_resume_text
from .types import JobRunResult
from .utils import slugify


def run_option2(data_dir: Path, out_dir: Path, limit: int | None = None) -> None:
    settings = load_settings()

    jobs = load_jobs(data_dir)
    if limit is not None:
        jobs = jobs[:limit]

    base_resume_text = load_base_resume_text(data_dir)
    out_dir_resumes = out_dir / "resumes"
    out_dir_emails = out_dir / "emails"
    out_dir_reports = out_dir

    results: list[JobRunResult] = []

    print(f"Loaded {len(jobs)} jobs. Starting tailoring...")

    for idx, job in enumerate(jobs, start=1):
        print(f"[{idx}/{len(jobs)}] Processing job id={job.id} title={job.title}")
        try:
            tailored, detail = tailor_resume(settings, job, base_resume_text)
            resume_file = out_dir_resumes / f"resume_{job.id}_{slugify(job.title)}.docx"
            generate_tailored_docx(job, tailored, resume_file)

            email_status = send_tailored_resume_email(
                settings=settings,
                job=job,
                attachment_path=resume_file,
                out_dir=out_dir_emails,
            )

            results.append(
                JobRunResult(
                    job=job,
                    status="success",
                    output_resume_path=str(resume_file),
                    error=None,
                )
            )
            print(f"  Success: {resume_file.name} ({detail}, email={email_status})")
        except Exception as e:
            err = "".join(traceback.format_exception(type(e), e, e.__traceback__))
            results.append(
                JobRunResult(
                    job=job,
                    status="failed",
                    output_resume_path=None,
                    error=err,
                )
            )
            print(f"  Failed: job id={job.id}. Error: {e}")

    report_path = out_dir_reports / "run_report.json"
    report_path.write_text(json.dumps([r.model_dump() for r in results], indent=2), encoding="utf-8")
    print(f"Done. Wrote report: {report_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Option 2: AI Resume Tailoring Agent")
    parser.add_argument("--data-dir", default="inputs", help="Directory containing option2 input files.")
    parser.add_argument("--out-dir", default="outputs", help="Directory to write resumes and emails.")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for debugging.")
    parser.add_argument("--dry-run", action="store_true", help="Write .eml files instead of sending email.")
    args = parser.parse_args()

    # Load .env if present (so README instructions work out of the box).
    load_dotenv(override=False)

    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    run_option2(Path(args.data_dir), Path(args.out_dir), limit=args.limit)


if __name__ == "__main__":
    main()

