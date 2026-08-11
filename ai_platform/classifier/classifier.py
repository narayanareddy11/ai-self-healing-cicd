from __future__ import annotations

from ai_platform.models.state import FailureCategory


class FailureClassifier:
    def classify(self, job_name: str, step_name: str, logs: str = "") -> FailureCategory:
        signal = f"{job_name} {step_name} {logs}".lower()

        if any(token in signal for token in ("pytest", "assertionerror", "unit tests")):
            return FailureCategory.UNIT_TEST
        if any(token in signal for token in ("bandit", "trivy", "cve-", "security scan")):
            return FailureCategory.SECURITY
        if any(token in signal for token in ("docker build", "dockerfile", "failed to solve")):
            return FailureCategory.DOCKER
        if any(token in signal for token in ("kubectl", "kubernetes", "deployment", "manifest")):
            return FailureCategory.KUBERNETES
        if any(token in signal for token in ("workflow", "github actions", "yaml", "unable to resolve action")):
            return FailureCategory.GITHUB_ACTIONS
        if any(token in signal for token in ("pip install", "modulenotfounderror", "syntaxerror")):
            return FailureCategory.PYTHON_BUILD

        return FailureCategory.UNKNOWN
