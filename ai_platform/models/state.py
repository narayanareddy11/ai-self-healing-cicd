from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, Field


class FailureCategory(StrEnum):
    PYTHON_BUILD = "PYTHON_BUILD"
    UNIT_TEST = "UNIT_TEST"
    SECURITY = "SECURITY"
    DOCKER = "DOCKER"
    KUBERNETES = "KUBERNETES"
    GITHUB_ACTIONS = "GITHUB_ACTIONS"
    UNKNOWN = "UNKNOWN"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class VerificationStatus(StrEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class IncidentStatus(StrEnum):
    RECEIVED = "RECEIVED"
    CLASSIFIED = "CLASSIFIED"
    EVIDENCE_COLLECTED = "EVIDENCE_COLLECTED"
    RCA_COMPLETED = "RCA_COMPLETED"
    REMEDIATION_GENERATED = "REMEDIATION_GENERATED"
    GUARDRAIL_BLOCKED = "GUARDRAIL_BLOCKED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"
    PR_CREATED = "PR_CREATED"
    REPORTED = "REPORTED"


class FailureEvent(BaseModel):
    incident_id: str
    repository: str
    workflow_name: str
    workflow_run_id: int
    commit_sha: str
    branch: str
    failed_job: str
    failed_step: str
    conclusion: str = "failure"
    html_url: str | None = None
    timestamp: str | None = None


class EvidenceItem(BaseModel):
    source: str
    kind: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceBundle(BaseModel):
    incident_id: str
    items: list[EvidenceItem] = Field(default_factory=list)
    changed_files: list[str] = Field(default_factory=list)


class RCAResult(BaseModel):
    failure_type: FailureCategory
    root_cause: str
    observed_evidence: list[str]
    inference: str
    recommended_fix: str
    files_to_modify: list[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel


class ProposedFix(BaseModel):
    summary: str
    files_to_modify: list[str]
    diff: str
    commands_to_run: list[str] = Field(default_factory=list)


class VerificationResult(BaseModel):
    status: VerificationStatus
    commands: list[str] = Field(default_factory=list)
    output: str = ""


class PullRequestPlan(BaseModel):
    branch_name: str
    title: str
    body: str
    files_changed: list[str]


class RemediationState(TypedDict, total=False):
    incident_id: str
    repository: str
    workflow_name: str
    workflow_run_id: int
    commit_sha: str
    branch: str
    failed_job: str
    failed_step: str
    raw_logs: str
    failure_category: str
    evidence: dict[str, Any]
    root_cause: dict[str, Any]
    confidence_score: float
    risk_score: float
    proposed_fix: dict[str, Any]
    verification_results: dict[str, Any]
    pr_url: str
    status: str
    guardrail_reason: str
    validation_route: Literal["create_pr", "report_failure"]
