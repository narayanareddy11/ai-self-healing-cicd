from __future__ import annotations

import hashlib
from typing import Any

from ai_platform.models.state import FailureEvent


def parse_workflow_failure(payload: dict[str, Any]) -> FailureEvent | None:
    workflow_run = payload.get("workflow_run") or {}
    if workflow_run.get("conclusion") != "failure":
        return None

    repository = payload.get("repository") or {}
    repo_full_name = repository.get("full_name")
    run_id = workflow_run.get("id")
    head_sha = workflow_run.get("head_sha")
    branch = workflow_run.get("head_branch")
    workflow_name = workflow_run.get("name") or payload.get("workflow", {}).get("name") or "unknown"

    if not repo_full_name or not run_id or not head_sha or not branch:
        raise ValueError("workflow_run payload is missing required failure metadata")

    incident_key = f"{repo_full_name}:{run_id}:{head_sha}"
    incident_id = hashlib.sha256(incident_key.encode()).hexdigest()[:12]

    return FailureEvent(
        incident_id=incident_id,
        repository=repo_full_name,
        workflow_name=workflow_name,
        workflow_run_id=int(run_id),
        commit_sha=head_sha,
        branch=branch,
        failed_job=workflow_run.get("display_title") or "unknown",
        failed_step="unknown",
        conclusion="failure",
        html_url=workflow_run.get("html_url"),
        timestamp=workflow_run.get("updated_at"),
    )
