from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from ai_platform.agents.router import RCAAgentRouter
from ai_platform.classifier.classifier import FailureClassifier
from ai_platform.collectors.evidence import EvidenceCollector
from ai_platform.github.client import GitHubPullRequestClient
from ai_platform.models.state import (
    EvidenceBundle,
    FailureCategory,
    FailureEvent,
    IncidentStatus,
    RCAResult,
    RemediationState,
    VerificationStatus,
)
from ai_platform.remediation.engine import RemediationEngine
from ai_platform.remediation.guardrails import GuardrailEngine
from ai_platform.verification.runner import VerificationRunner


class RemediationGraph:
    def __init__(
        self,
        classifier: FailureClassifier | None = None,
        evidence_collector: EvidenceCollector | None = None,
        router: RCAAgentRouter | None = None,
        remediation_engine: RemediationEngine | None = None,
        guardrails: GuardrailEngine | None = None,
        verifier: VerificationRunner | None = None,
        github: GitHubPullRequestClient | None = None,
        create_pr: bool = False,
    ) -> None:
        self.classifier = classifier or FailureClassifier()
        self.evidence_collector = evidence_collector or EvidenceCollector()
        self.router = router or RCAAgentRouter()
        self.remediation_engine = remediation_engine or RemediationEngine()
        self.guardrails = guardrails or GuardrailEngine()
        self.verifier = verifier or VerificationRunner()
        self.github = github or GitHubPullRequestClient()
        self.create_pr_enabled = create_pr
        self.graph = self._build_graph()

    def invoke(self, event: FailureEvent, logs: str, changed_files: list[str] | None = None) -> RemediationState:
        initial: RemediationState = {
            **event.model_dump(),
            "raw_logs": logs,
            "evidence": {"changed_files": changed_files or []},
            "status": IncidentStatus.RECEIVED.value,
        }
        return self.graph.invoke(initial)

    def _build_graph(self):
        builder = StateGraph(RemediationState)
        builder.add_node("classify_failure", self._classify_failure)
        builder.add_node("collect_evidence", self._collect_evidence)
        builder.add_node("generate_rca", self._generate_rca)
        builder.add_node("generate_fix", self._generate_fix)
        builder.add_node("validate_guardrails", self._validate_guardrails)
        builder.add_node("verify_fix", self._verify_fix)
        builder.add_node("create_pr", self._create_pr)
        builder.add_node("report_failure", self._report_failure)

        builder.add_edge(START, "classify_failure")
        builder.add_edge("classify_failure", "collect_evidence")
        builder.add_edge("collect_evidence", "generate_rca")
        builder.add_edge("generate_rca", "generate_fix")
        builder.add_edge("generate_fix", "validate_guardrails")
        builder.add_conditional_edges(
            "validate_guardrails",
            self._guardrail_route,
            {"verify_fix": "verify_fix", "report_failure": "report_failure"},
        )
        builder.add_conditional_edges(
            "verify_fix",
            self._verification_route,
            {"create_pr": "create_pr", "report_failure": "report_failure"},
        )
        builder.add_edge("create_pr", END)
        builder.add_edge("report_failure", END)
        return builder.compile()

    def _event_from_state(self, state: RemediationState) -> FailureEvent:
        return FailureEvent(
            incident_id=state["incident_id"],
            repository=state["repository"],
            workflow_name=state["workflow_name"],
            workflow_run_id=state["workflow_run_id"],
            commit_sha=state["commit_sha"],
            branch=state["branch"],
            failed_job=state["failed_job"],
            failed_step=state["failed_step"],
        )

    def _classify_failure(self, state: RemediationState) -> RemediationState:
        category = self.classifier.classify(
            state.get("failed_job", ""),
            state.get("failed_step", ""),
            state.get("raw_logs", ""),
        )
        return {"failure_category": category.value, "status": IncidentStatus.CLASSIFIED.value}

    def _collect_evidence(self, state: RemediationState) -> RemediationState:
        event = self._event_from_state(state)
        category = FailureCategory(state["failure_category"])
        changed_files = state.get("evidence", {}).get("changed_files", [])
        evidence = self.evidence_collector.collect(event, category, state.get("raw_logs", ""), changed_files)
        return {"evidence": evidence.model_dump(), "status": IncidentStatus.EVIDENCE_COLLECTED.value}

    def _generate_rca(self, state: RemediationState) -> RemediationState:
        category = FailureCategory(state["failure_category"])
        evidence = EvidenceBundle.model_validate(state["evidence"])
        rca = self.router.select(category).analyze(evidence)
        return {
            "root_cause": rca.model_dump(mode="json"),
            "confidence_score": rca.confidence_score,
            "risk_score": {"LOW": 0.2, "MEDIUM": 0.5, "HIGH": 0.9}[rca.risk_level.value],
            "status": IncidentStatus.RCA_COMPLETED.value,
        }

    def _generate_fix(self, state: RemediationState) -> RemediationState:
        rca = RCAResult.model_validate(state["root_cause"])
        fix = self.remediation_engine.generate(rca)
        return {"proposed_fix": fix.model_dump(), "status": IncidentStatus.REMEDIATION_GENERATED.value}

    def _validate_guardrails(self, state: RemediationState) -> RemediationState:
        from ai_platform.models.state import ProposedFix

        fix = ProposedFix.model_validate(state["proposed_fix"])
        result = self.guardrails.validate(fix)
        if not result.allowed:
            return {
                "guardrail_reason": result.reason,
                "validation_route": "report_failure",
                "status": IncidentStatus.GUARDRAIL_BLOCKED.value,
            }
        return {"validation_route": "create_pr"}

    def _verify_fix(self, state: RemediationState) -> RemediationState:
        from ai_platform.models.state import ProposedFix

        fix = ProposedFix.model_validate(state["proposed_fix"])
        result = self.verifier.run(fix.commands_to_run)
        status = (
            IncidentStatus.REMEDIATION_GENERATED
            if result.status == VerificationStatus.PASSED
            else IncidentStatus.VERIFICATION_FAILED
        )
        return {"verification_results": result.model_dump(), "status": status.value}

    def _create_pr(self, state: RemediationState) -> RemediationState:
        from ai_platform.models.state import VerificationResult

        event = self._event_from_state(state)
        rca = RCAResult.model_validate(state["root_cause"])
        verification = VerificationResult.model_validate(state["verification_results"])
        plan = self.github.build_plan(event, rca, verification)
        pr_url = self.github.create_pr(plan) if self.create_pr_enabled else f"dry-run:{plan.branch_name}"
        return {"pr_url": pr_url, "status": IncidentStatus.PR_CREATED.value}

    def _report_failure(self, state: RemediationState) -> RemediationState:
        return {"status": IncidentStatus.REPORTED.value}

    def _guardrail_route(self, state: RemediationState) -> str:
        return "report_failure" if state.get("validation_route") == "report_failure" else "verify_fix"

    def _verification_route(self, state: RemediationState) -> str:
        verification = state.get("verification_results", {})
        return "create_pr" if verification.get("status") == VerificationStatus.PASSED.value else "report_failure"
