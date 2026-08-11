from __future__ import annotations

import hashlib
import hmac


def build_signature(secret: str, payload: bytes) -> str:
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def verify_signature(secret: str, payload: bytes, signature_header: str | None) -> bool:
    if not secret or not signature_header:
        return False
    expected = build_signature(secret, payload)
    return hmac.compare_digest(expected, signature_header)
