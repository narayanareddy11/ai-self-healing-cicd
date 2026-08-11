from __future__ import annotations

from dataclasses import dataclass

from ai_platform.models.state import ProposedFix

FORBIDDEN_DIFF_PATTERNS = (
    "GITHUB_TOKEN",
    "GITHUB_SECRET",
    "auto-merge",
    "automerge",
    "bandit -x",
    "trivy --skip",
    "pytest -k 'not",
    "kubectl delete",
    "rm -rf",
)


@dataclass(frozen=True)
class GuardrailResult:
    allowed: bool
    reason: str = ""


class GuardrailEngine:
    def validate(self, fix: ProposedFix) -> GuardrailResult:
        diff_lower = fix.diff.lower()
        for pattern in FORBIDDEN_DIFF_PATTERNS:
            if pattern.lower() in diff_lower:
                return GuardrailResult(False, f"Forbidden remediation pattern: {pattern}")

        for path in fix.files_to_modify:
            if path.startswith("/") or ".." in path.split("/"):
                return GuardrailResult(False, f"File path is outside repository scope: {path}")
            if path == ".github/workflows/ci.yml" and "bandit" in diff_lower and "-r services" not in diff_lower:
                return GuardrailResult(False, "Security scanner modification is not allowed")

        return GuardrailResult(True)
