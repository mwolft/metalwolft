"""Public, non-persistent security reporting endpoints."""

from collections import deque
import hashlib
import json
import math
import threading
import time
from urllib.parse import urlsplit

from flask import Blueprint, current_app, request


security_bp = Blueprint("security", __name__)

CSP_REPORT_MAX_BYTES = 8_192
CSP_REPORT_MAX_REPORTS = 10
CSP_REPORT_RATE_LIMIT_REQUESTS = 30
CSP_REPORT_RATE_LIMIT_WINDOW_SECONDS = 60
CSP_REPORT_GLOBAL_RATE_LIMIT_REQUESTS = 300
CSP_REPORT_CONTENT_TYPES = frozenset(
    {
        "application/csp-report",
        "application/json",
        "application/reports+json",
    }
)
_CSP_REPORT_URI_TOKENS = frozenset(
    {"about", "blob", "data", "eval", "inline", "none", "self", "wasm-eval"}
)


class _CspReportRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._client_requests = {}
        self._global_requests = deque()
        self._last_cleanup = 0

    @staticmethod
    def _prune(entries, cutoff):
        while entries and entries[0] <= cutoff:
            entries.popleft()

    def allow(self, client_key):
        now = time.monotonic()
        cutoff = now - CSP_REPORT_RATE_LIMIT_WINDOW_SECONDS

        with self._lock:
            self._prune(self._global_requests, cutoff)
            if now - self._last_cleanup >= CSP_REPORT_RATE_LIMIT_WINDOW_SECONDS:
                for existing_key, entries in list(self._client_requests.items()):
                    self._prune(entries, cutoff)
                    if not entries:
                        del self._client_requests[existing_key]
                self._last_cleanup = now

            client_entries = self._client_requests.setdefault(client_key, deque())
            self._prune(client_entries, cutoff)
            limit_reached = len(self._global_requests) >= CSP_REPORT_GLOBAL_RATE_LIMIT_REQUESTS
            limit_reached = limit_reached or len(client_entries) >= CSP_REPORT_RATE_LIMIT_REQUESTS
            if limit_reached:
                oldest = max(
                    self._global_requests[0] if self._global_requests else now,
                    client_entries[0] if client_entries else now,
                )
                retry_after = math.ceil(
                    CSP_REPORT_RATE_LIMIT_WINDOW_SECONDS - (now - oldest)
                )
                return False, max(1, retry_after)

            client_entries.append(now)
            self._global_requests.append(now)
            return True, None

    def reset(self):
        with self._lock:
            self._client_requests.clear()
            self._global_requests.clear()
            self._last_cleanup = 0


_csp_report_rate_limiter = _CspReportRateLimiter()


def _client_key():
    client_address = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
        or request.remote_addr
        or "unknown"
    )
    return hashlib.sha256(client_address.encode("utf-8")).hexdigest()


def _sanitize_url(value):
    if not isinstance(value, str):
        return None

    value = value.strip()
    if value.lower() in _CSP_REPORT_URI_TOKENS:
        return value.lower()

    try:
        parsed = urlsplit(value)
    except ValueError:
        return None

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None

    origin = f"{parsed.scheme}://{parsed.hostname.lower()}"
    try:
        port = parsed.port
    except ValueError:
        return None
    if port:
        origin += f":{port}"
    path = parsed.path[:256]
    return f"{origin}{path}"


def _sanitize_directive(value):
    if not isinstance(value, str):
        return None

    normalized = " ".join(value.lower().split())[:160]
    if not normalized or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-'_ " for character in normalized):
        return None
    return normalized


def _sanitize_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if 0 <= number <= 1_000_000 else None


def _normalize_report(report):
    if not isinstance(report, dict):
        return None

    normalized = {
        "blocked_uri": _sanitize_url(report.get("blocked-uri", report.get("blockedURL"))),
        "violated_directive": _sanitize_directive(
            report.get("violated-directive", report.get("violatedDirective"))
        ),
        "effective_directive": _sanitize_directive(
            report.get("effective-directive", report.get("effectiveDirective"))
        ),
        "document_uri": _sanitize_url(report.get("document-uri", report.get("documentURL"))),
        "source_file": _sanitize_url(report.get("source-file", report.get("sourceFile"))),
        "line_number": _sanitize_number(report.get("line-number", report.get("lineNumber"))),
        "column_number": _sanitize_number(report.get("column-number", report.get("columnNumber"))),
        "disposition": _sanitize_directive(report.get("disposition")),
    }
    if not (normalized["violated_directive"] or normalized["effective_directive"]):
        return None
    return {key: value for key, value in normalized.items() if value is not None}


def _extract_reports(payload):
    if isinstance(payload, dict):
        if isinstance(payload.get("csp-report"), dict):
            return [payload["csp-report"]]
        if isinstance(payload.get("body"), dict):
            return [payload["body"]]
        return [payload]

    if isinstance(payload, list):
        return [entry["body"] for entry in payload if isinstance(entry, dict) and isinstance(entry.get("body"), dict)]
    return []


@security_bp.route("/security/csp-report", methods=["POST"])
def csp_report():
    if request.mimetype not in CSP_REPORT_CONTENT_TYPES:
        return "", 415

    if request.content_length is not None and request.content_length > CSP_REPORT_MAX_BYTES:
        return "", 413

    raw_body = request.stream.read(CSP_REPORT_MAX_BYTES + 1)
    if len(raw_body) > CSP_REPORT_MAX_BYTES:
        return "", 413

    allowed, retry_after = _csp_report_rate_limiter.allow(_client_key())
    if not allowed:
        response = current_app.response_class(status=429)
        response.headers["Retry-After"] = str(retry_after)
        return response

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "", 400

    reports = _extract_reports(payload)
    if not reports or len(reports) > CSP_REPORT_MAX_REPORTS:
        return "", 400

    normalized_reports = [
        normalized for report in reports if (normalized := _normalize_report(report)) is not None
    ]
    if not normalized_reports:
        return "", 400

    current_app.logger.info(
        json.dumps(
            {"event": "csp_violation_report", "reports": normalized_reports},
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return "", 204
