from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import List

from .config import Settings
from .types import JobDetails
from .utils import ensure_dir


def _parse_recipients(email_to: str) -> List[str]:
    return [e.strip() for e in email_to.split(",") if e.strip()]


def send_tailored_resume_email(
    settings: Settings,
    job: JobDetails,
    attachment_path: Path,
    out_dir: Path,
) -> str:
    """
    Sends or writes a draft email containing a DOCX attachment.

    Returns a status string for run_report.
    """

    recipients = _parse_recipients(settings.email_to)
    if not recipients:
        raise ValueError("EMAIL_TO is empty or invalid.")

    subject = f"{job.title} - Tailored Resume ({job.company})"
    body = (
        f"Hi,\n\n"
        f"Attached is a tailored resume for:\n"
        f"- Job Title: {job.title}\n"
        f"- Company: {job.company}\n"
        f"- Job URL: {job.url}\n\n"
        f"Regards,\n"
        f"AI Resume Tailoring Agent"
    )

    msg = EmailMessage()
    msg["From"] = settings.email_from
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    doc_bytes = attachment_path.read_bytes()
    msg.add_attachment(
        doc_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=attachment_path.name,
    )

    ensure_dir(out_dir)
    if settings.dry_run:
        eml_path = out_dir / f"resume_email_job_{job.id}.eml"
        eml_path.write_bytes(msg.as_bytes())
        return f"dry_run_wrote_{eml_path.name}"

    # Real SMTP send.
    if settings.smtp_use_ssl:
        smtp = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30)
    else:
        smtp = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30)

    try:
        smtp.ehlo()
        if settings.smtp_use_tls and not settings.smtp_use_ssl:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(msg)
    finally:
        try:
            smtp.quit()
        except Exception:
            pass

    return "sent"

