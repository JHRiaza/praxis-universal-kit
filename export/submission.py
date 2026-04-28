"""PRAXIS export delivery helpers.

Supports optional SMTP submission with throttling so the study can scale
without flooding the research inbox.
"""

from __future__ import annotations

import json
import os
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_SETTINGS: Dict[str, Any] = {
    "enabled": False,
    "mode": "smtp",
    "email_to": "hello@javierherreros.xyz",
    "cooldown_hours": 168,
    "max_submissions_per_30d": 4,
}
LOG_FILE = "submission_log.jsonl"
CONFIG_FILE = "submission.json"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _log_path(praxis_dir: Path) -> Path:
    return praxis_dir / LOG_FILE


def _config_path(praxis_dir: Path) -> Path:
    return praxis_dir / CONFIG_FILE


def load_submission_settings(praxis_dir: Path) -> Dict[str, Any]:
    settings = dict(DEFAULT_SETTINGS)
    path = _config_path(praxis_dir)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                settings.update(data)
        except Exception:
            pass
    return settings


def read_submission_log(praxis_dir: Path) -> List[Dict[str, Any]]:
    path = _log_path(praxis_dir)
    if not path.is_file():
        return []
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def record_submission(praxis_dir: Path, event: Dict[str, Any]) -> None:
    path = _log_path(praxis_dir)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False) + "\n")


def get_submission_status(praxis_dir: Path) -> Dict[str, Any]:
    settings = load_submission_settings(praxis_dir)
    logs = read_submission_log(praxis_dir)
    now = _now()
    last_success = None
    success_rows = []
    for row in logs:
        if row.get("status") != "sent":
            continue
        success_rows.append(row)
        try:
            ts = datetime.fromisoformat(str(row.get("timestamp", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if last_success is None or ts > last_success:
            last_success = ts

    sent_30d = 0
    for row in success_rows:
        try:
            ts = datetime.fromisoformat(str(row.get("timestamp", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if ts >= now - timedelta(days=30):
            sent_30d += 1

    cooldown_remaining_hours = 0
    allowed = bool(settings.get("enabled"))
    reason = "Submission is disabled."

    if not settings.get("enabled"):
        allowed = False
        reason = "Submission is disabled in .praxis/submission.json."
    else:
        cooldown = int(settings.get("cooldown_hours", 168) or 0)
        limit = int(settings.get("max_submissions_per_30d", 4) or 0)
        if last_success and cooldown > 0:
            next_allowed = last_success + timedelta(hours=cooldown)
            if next_allowed > now:
                cooldown_remaining_hours = int((next_allowed - now).total_seconds() // 3600) + 1
                allowed = False
                reason = f"Cooldown active for ~{cooldown_remaining_hours} more hour(s)."
        if allowed and limit > 0 and sent_30d >= limit:
            allowed = False
            reason = f"Monthly submission limit reached ({sent_30d}/{limit} in last 30 days)."
        if allowed:
            reason = "Ready to submit."

    return {
        "settings": settings,
        "allowed": allowed,
        "reason": reason,
        "last_submitted_at": last_success.isoformat() if last_success else None,
        "sent_last_30d": sent_30d,
        "cooldown_remaining_hours": cooldown_remaining_hours,
    }


def _smtp_config_from_env() -> Dict[str, Any]:
    return {
        "host": os.getenv("PRAXIS_SMTP_HOST", "").strip(),
        "port": int(os.getenv("PRAXIS_SMTP_PORT", "587") or "587"),
        "user": os.getenv("PRAXIS_SMTP_USER", "").strip(),
        "password": os.getenv("PRAXIS_SMTP_PASS", "").strip(),
        "from": os.getenv("PRAXIS_SMTP_FROM", os.getenv("PRAXIS_SMTP_USER", "")).strip(),
        "tls": os.getenv("PRAXIS_SMTP_TLS", "true").strip().lower() not in {"0", "false", "no"},
    }


def submit_export(
    praxis_dir: Path,
    zip_path: Path,
    participant_id: str,
    diagnosis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    status = get_submission_status(praxis_dir)
    if not status["allowed"]:
        raise RuntimeError(status["reason"])

    settings = status["settings"]
    if settings.get("mode") != "smtp":
        raise RuntimeError("Only SMTP delivery is currently implemented.")

    smtp = _smtp_config_from_env()
    missing = [key for key in ("host", "user", "password", "from") if not smtp.get(key)]
    if missing:
        raise RuntimeError(
            "SMTP is not configured. Set PRAXIS_SMTP_HOST, PRAXIS_SMTP_USER, PRAXIS_SMTP_PASS, and PRAXIS_SMTP_FROM."
        )

    to_addr = settings.get("email_to") or DEFAULT_SETTINGS["email_to"]
    subject = f"PRAXIS submission [{participant_id}]"
    diag_headline = (diagnosis or {}).get("headline", "")
    body = [
        "PRAXIS automated submission",
        "",
        f"Participant ID: {participant_id}",
        f"Generated at: {_now_iso()}",
        f"Attachment: {zip_path.name}",
    ]
    if diag_headline:
        body.extend(["", f"Workflow diagnosis: {diag_headline}"])

    msg = EmailMessage()
    msg["From"] = smtp["from"]
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content("\n".join(body))
    msg.add_attachment(zip_path.read_bytes(), maintype="application", subtype="zip", filename=zip_path.name)

    try:
        with smtplib.SMTP(smtp["host"], smtp["port"], timeout=30) as server:
            if smtp["tls"]:
                server.starttls()
            server.login(smtp["user"], smtp["password"])
            server.send_message(msg)
    except Exception as exc:
        record_submission(
            praxis_dir,
            {
                "timestamp": _now_iso(),
                "status": "failed",
                "participant_id": participant_id,
                "zip_name": zip_path.name,
                "error": str(exc),
            },
        )
        raise RuntimeError(f"SMTP submission failed: {exc}") from exc

    record_submission(
        praxis_dir,
        {
            "timestamp": _now_iso(),
            "status": "sent",
            "participant_id": participant_id,
            "zip_name": zip_path.name,
            "mode": "smtp",
            "email_to": to_addr,
        },
    )

    return {
        "status": "sent",
        "participant_id": participant_id,
        "zip_name": zip_path.name,
        "email_to": to_addr,
    }


def submission_setup_template() -> str:
    return json.dumps(DEFAULT_SETTINGS, indent=2, ensure_ascii=False) + "\n"
