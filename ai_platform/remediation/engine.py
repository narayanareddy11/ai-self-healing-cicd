from __future__ import annotations

from ai_platform.models.state import FailureCategory, ProposedFix, RCAResult


class RemediationEngine:
    def generate(self, rca: RCAResult) -> ProposedFix:
        if rca.failure_type == FailureCategory.GITHUB_ACTIONS:
            return ProposedFix(
                summary="Update GitHub Actions workflow configuration.",
                files_to_modify=rca.files_to_modify or [".github/workflows/ci.yml"],
                diff="Workflow configuration should be updated according to the RCA evidence.",
                commands_to_run=["python scripts/validate-kubernetes-manifests.py"],
            )

        if rca.failure_type == FailureCategory.UNIT_TEST:
            return ProposedFix(
                summary="Fix failing unit test behavior.",
                files_to_modify=rca.files_to_modify,
                diff="Application or test code should be updated to satisfy the failing assertion.",
                commands_to_run=[
                    "python -m ruff check services ai_platform tests scripts",
                    "python -m pytest",
                ],
            )

        return ProposedFix(
            summary=rca.recommended_fix,
            files_to_modify=rca.files_to_modify,
            diff="No automatic patch generated for this failure category yet.",
            commands_to_run=[],
        )
