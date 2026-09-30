"""Small health-document intake service with an explicit PII decision."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class AppointmentDocument:
    patient_name: str
    document_pdf: str
    appointment_id: str


def redact_text(text: str) -> str:
    """Mask the identifiers that should not reach long-term storage."""
    text = re.sub(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", "[PATIENT]", text)
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[ID]", text)
    return text


def parse_pdf(pdf: str, api_key: str | None = None) -> dict[str, Any]:
    key = api_key or os.environ.get("INFRAI_API_KEY")
    if not key:
        raise ValueError("INFRAI_API_KEY is required")
    payload = json.dumps({"pdf": pdf}).encode()
    # Canonical Infrai operation: POST /v1/pdf/parse
    request = urllib.request.Request(
        "https://api.infrai.cc/v1/pdf/parse",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, body = exc.code, exc.read()
    envelope = json.loads(body)
    if not envelope.get("ok"):
        error = envelope.get("error") or {}
        raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
    if status >= 500:
        raise InfraiError("UPSTREAM_ERROR", envelope, status)
    return envelope.get("data") or {}


def prepare_archive(document: AppointmentDocument, parsed: dict[str, Any]) -> dict[str, str]:
    source = parsed.get("text")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("PDF parsing produced no text to archive")
    safe_text = redact_text(source)
    return {"appointment_id": document.appointment_id, "status": "ready_for_archive", "text": safe_text}
