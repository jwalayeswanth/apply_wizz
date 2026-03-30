from __future__ import annotations

import json
from pathlib import Path
from typing import List

import pandas as pd

from .types import JobDetails


REQUIRED_EXCEL_COLUMNS = ["#", "Job Title", "Company", "URL", "Resume Path"]


def load_jobs(data_dir: Path) -> List[JobDetails]:
    """
    Join:
      - option2_job_links.xlsx (Excel rows; keyed by "#")
      - option2_jobs.json (jobs[]; keyed by "id")
    """

    excel_path = data_dir / "option2_job_links.xlsx"
    json_path = data_dir / "option2_jobs.json"

    if not excel_path.exists():
        raise FileNotFoundError(f"Missing Excel file: {excel_path}")
    if not json_path.exists():
        raise FileNotFoundError(f"Missing JSON file: {json_path}")

    df = pd.read_excel(excel_path)

    missing = [c for c in REQUIRED_EXCEL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Excel is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    jobs = raw.get("jobs", [])
    jobs_by_id = {j["id"]: j for j in jobs if "id" in j}

    results: List[JobDetails] = []
    for i, row in df.iterrows():
        job_id = int(row["#"])
        json_job = jobs_by_id.get(job_id)
        if not json_job:
            raise KeyError(f"Job id {job_id} found in Excel but not in option2_jobs.json.")

        results.append(
            JobDetails(
                id=job_id,
                title=str(row["Job Title"]),
                company=str(row["Company"]),
                url=str(row["URL"]),
                description=str(json_job.get("description", "")),
                requirements=list(json_job.get("requirements", [])),
                nice_to_have=list(json_job.get("nice_to_have", [])),
            )
        )

    return results

