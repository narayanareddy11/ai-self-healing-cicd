from __future__ import annotations

import re

SECRET_PATTERNS = [
    re.compile(r"(?i)(token|secret|password|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s]+"),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
]


def redact_secrets(value: str) -> str:
    redacted = value
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub(lambda match: match.group(0).split("=", 1)[0] + "=<REDACTED>", redacted)
    return redacted
