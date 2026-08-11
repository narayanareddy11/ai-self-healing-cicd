from __future__ import annotations

import subprocess  # nosec B404

from ai_platform.models.state import FailureEvent, PullRequestPlan, RCAResult, VerificationResult


class GitHubPullRequestClient:
    def build_plan(
        self,
        event: FailureEvent,
        rca: RCAResult,
        verification: VerificationResult,
    ) -> PullRequestPlan:
        branch_name = f"ai-remediation/{event.incident_id}"
        title = f"[AI Remediation] Fix {rca.failure_type.value} failure"
        body = "\n".join(
            [
                "AI-generated remediation. Human review is required.",
                "",
                f"Incident: {event.incident_id}",
                f"Workflow: {event.workflow_name}",
                f"Workflow run ID: {event.workflow_run_id}",
                f"Commit: {event.commit_sha}",
                f"Failed job: {event.failed_job}",
                f"Failed step: {event.failed_step}",
                "",
                f"Root cause: {rca.root_cause}",
                f"Inference: {rca.inference}",
                f"Recommended fix: {rca.recommended_fix}",
                f"Files changed: {', '.join(rca.files_to_modify) or 'none'}",
                f"Verification status: {verification.status.value}",
                f"Verification commands: {', '.join(verification.commands) or 'none'}",
                f"Confidence score: {rca.confidence_score}",
                f"Risk level: {rca.risk_level.value}",
            ]
        )
        return PullRequestPlan(branch_name=branch_name, title=title, body=body, files_changed=rca.files_to_modify)

    def create_pr(self, plan: PullRequestPlan, base_branch: str = "main") -> str:
        subprocess.run(["git", "switch", "-c", plan.branch_name], check=True)  # nosec B603 B607
        subprocess.run(["git", "add", *plan.files_changed], check=True)  # nosec B603 B607
        subprocess.run(["git", "commit", "-m", plan.title], check=True)  # nosec B603 B607
        subprocess.run(["git", "push", "-u", "origin", plan.branch_name], check=True)  # nosec B603 B607
        completed = subprocess.run(
            ["gh", "pr", "create", "--base", base_branch, "--title", plan.title, "--body", plan.body],
            check=True,
            capture_output=True,
            text=True,
        )  # nosec B603 B607
        return completed.stdout.strip()
