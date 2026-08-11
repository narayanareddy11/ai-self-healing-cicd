from __future__ import annotations

from ai_platform.collectors.redaction import redact_secrets
from ai_platform.models.state import EvidenceBundle, EvidenceItem, FailureCategory, FailureEvent


class EvidenceCollector:
    def collect(
        self,
        event: FailureEvent,
        category: FailureCategory,
        logs: str,
        changed_files: list[str] | None = None,
    ) -> EvidenceBundle:
        focused_logs = self._focused_log_section(category, logs)
        return EvidenceBundle(
            incident_id=event.incident_id,
            changed_files=changed_files or [],
            items=[
                EvidenceItem(
                    source="github_actions",
                    kind="failure_metadata",
                    content=event.model_dump_json(),
                    metadata={
                        "workflow": event.workflow_name,
                        "run_id": event.workflow_run_id,
                        "commit_sha": event.commit_sha,
                        "branch": event.branch,
                    },
                ),
                EvidenceItem(
                    source="github_actions",
                    kind="focused_logs",
                    content=redact_secrets(focused_logs),
                    metadata={"failure_category": category.value},
                ),
            ],
        )

    def _focused_log_section(self, category: FailureCategory, logs: str) -> str:
        if not logs:
            return ""

        keywords = {
            FailureCategory.UNIT_TEST: ("failed", "assertionerror", "pytest", "traceback"),
            FailureCategory.DOCKER: ("error", "dockerfile", "failed to solve", "copy failed"),
            FailureCategory.KUBERNETES: ("error", "kubectl", "manifest", "deployment"),
            FailureCategory.SECURITY: ("high", "critical", "cve-", "bandit", "trivy"),
            FailureCategory.GITHUB_ACTIONS: ("error", "workflow", "yaml", "unable to resolve action"),
            FailureCategory.PYTHON_BUILD: ("error", "modulenotfounderror", "pip", "syntaxerror"),
            FailureCategory.UNKNOWN: ("error", "failed"),
        }[category]

        lines = logs.splitlines()
        matches: list[str] = []
        for index, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in keywords):
                start = max(0, index - 3)
                end = min(len(lines), index + 4)
                matches.extend(lines[start:end])

        if not matches:
            return "\n".join(lines[-80:])
        return "\n".join(dict.fromkeys(matches))[:8000]
