from __future__ import annotations

from ai_platform.classifier.classifier import FailureClassifier
from ai_platform.collectors.evidence import EvidenceCollector
from ai_platform.collectors.redaction import redact_secrets
from ai_platform.github.client import GitHubPullRequestClient
from ai_platform.models.state import (
    FailureCategory,
    FailureEvent,
    IncidentStatus,
    ProposedFix,
    RCAResult,
    RiskLevel,
    VerificationResult,
    VerificationStatus,
)
from ai_platform.orchestrator.graph import RemediationGraph
from ai_platform.remediation.guardrails import GuardrailEngine
from ai_platform.verification.runner import VerificationRunner
from ai_platform.webhook.parser import parse_workflow_failure
from ai_platform.webhook.signature import build_signature, verify_signature


def sample_event() -> FailureEvent:
    return FailureEvent(
        incident_id="inc123",
        repository="owner/repo",
        workflow_name="ci",
        workflow_run_id=100,
        commit_sha="abc123",
        branch="main",
        failed_job="python-quality",
        failed_step="Unit tests",
    )


def test_webhook_signature_validation() -> None:
    payload = b'{"ok": true}'
    signature = build_signature("secret", payload)

    assert verify_signature("secret", payload, signature)
    assert not verify_signature("secret", payload, "sha256=bad")


def test_parse_failed_workflow_run() -> None:
    event = parse_workflow_failure(
        {
            "repository": {"full_name": "owner/repo"},
            "workflow_run": {
                "id": 42,
                "conclusion": "failure",
                "head_sha": "abc",
                "head_branch": "main",
                "name": "ci",
                "display_title": "failing commit",
            },
        }
    )

    assert event is not None
    assert event.repository == "owner/repo"
    assert event.workflow_run_id == 42


def test_classifier_routes_unit_tests() -> None:
    category = FailureClassifier().classify("python-quality", "Unit tests", "AssertionError")

    assert category == FailureCategory.UNIT_TEST


def test_evidence_redacts_secrets() -> None:
    redacted = redact_secrets("token=ghp_abcdefghijklmnopqrstuvwxyz123456")

    assert "<REDACTED>" in redacted
    assert "ghp_" not in redacted


def test_evidence_collector_normalizes_logs() -> None:
    evidence = EvidenceCollector().collect(
        sample_event(),
        FailureCategory.UNIT_TEST,
        "line 1\nFAILED test_users\nAssertionError\npassword=secret-value",
        ["services/user-service/app/main.py"],
    )

    assert evidence.changed_files == ["services/user-service/app/main.py"]
    assert "password=<REDACTED>" in evidence.items[1].content


def test_guardrails_block_destructive_diff() -> None:
    fix = ProposedFix(
        summary="bad",
        files_to_modify=["kubernetes/user-service/deployment.yaml"],
        diff="run kubectl delete deployment user-service",
    )

    result = GuardrailEngine().validate(fix)

    assert not result.allowed
    assert "kubectl delete" in result.reason


def test_verification_blocks_non_allowlisted_command() -> None:
    result = VerificationRunner().run(["rm -rf /"])

    assert result.status == VerificationStatus.FAILED
    assert "not allowlisted" in result.output


def test_pr_plan_contains_human_review_notice() -> None:
    rca = RCAResult(
        failure_type=FailureCategory.UNIT_TEST,
        root_cause="A test failed.",
        observed_evidence=["pytest failed"],
        inference="Test behavior regression.",
        recommended_fix="Fix the assertion.",
        files_to_modify=["services/user-service/app/main.py"],
        confidence_score=0.8,
        risk_level=RiskLevel.LOW,
    )
    verification = VerificationResult(status=VerificationStatus.PASSED, commands=["python -m pytest"])

    plan = GitHubPullRequestClient().build_plan(sample_event(), rca, verification)

    assert plan.branch_name == "ai-remediation/inc123"
    assert "Human review is required" in plan.body
    assert "[AI Remediation]" in plan.title


def test_orchestrator_dry_run_creates_pr_plan_route() -> None:
    class PassingVerifier:
        def run(self, commands):
            return VerificationResult(status=VerificationStatus.PASSED, commands=list(commands))

    state = RemediationGraph(verifier=PassingVerifier()).invoke(
        sample_event(),
        "FAILED services/user-service/tests/test_main.py::test_list_users\nAssertionError",
        ["services/user-service/app/main.py"],
    )

    assert state["failure_category"] == FailureCategory.UNIT_TEST.value
    assert state["status"] == IncidentStatus.PR_CREATED.value
    assert state["pr_url"] == "dry-run:ai-remediation/inc123"
