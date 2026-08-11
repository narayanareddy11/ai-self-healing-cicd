from __future__ import annotations

from ai_platform.agents.base import RCAAgent
from ai_platform.models.state import EvidenceBundle, FailureCategory, RCAResult, RiskLevel


def _evidence_lines(evidence: EvidenceBundle) -> list[str]:
    return [item.content for item in evidence.items if item.kind == "focused_logs" and item.content]


class TestRCAAgent(RCAAgent):
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        return RCAResult(
            failure_type=FailureCategory.UNIT_TEST,
            root_cause="A unit test failed during the pytest step.",
            observed_evidence=_evidence_lines(evidence),
            inference="The failure is isolated to test/application behavior, not Docker or Kubernetes.",
            recommended_fix="Inspect the failing assertion or traceback and adjust the implementation or test.",
            files_to_modify=evidence.changed_files,
            confidence_score=0.82,
            risk_level=RiskLevel.LOW,
        )


class DockerRCAAgent(RCAAgent):
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        return RCAResult(
            failure_type=FailureCategory.DOCKER,
            root_cause="Docker image build failed.",
            observed_evidence=_evidence_lines(evidence),
            inference="The failure likely comes from the Dockerfile, build context, or dependency install layer.",
            recommended_fix="Update the Dockerfile or build context so the failing layer can complete.",
            files_to_modify=[path for path in evidence.changed_files if "Dockerfile" in path],
            confidence_score=0.78,
            risk_level=RiskLevel.MEDIUM,
        )


class KubernetesRCAAgent(RCAAgent):
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        return RCAResult(
            failure_type=FailureCategory.KUBERNETES,
            root_cause="Kubernetes validation or deployment failed.",
            observed_evidence=_evidence_lines(evidence),
            inference="The failure likely comes from manifest structure, image availability, or probe settings.",
            recommended_fix="Update the Kubernetes manifest and validate it before opening a PR.",
            files_to_modify=[path for path in evidence.changed_files if path.startswith("kubernetes/")],
            confidence_score=0.76,
            risk_level=RiskLevel.MEDIUM,
        )


class SecurityRCAAgent(RCAAgent):
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        return RCAResult(
            failure_type=FailureCategory.SECURITY,
            root_cause="Security scanner reported a blocking finding.",
            observed_evidence=_evidence_lines(evidence),
            inference="The fix should address the scanner finding without disabling the scanner.",
            recommended_fix="Upgrade the affected dependency or change the flagged code safely.",
            files_to_modify=evidence.changed_files,
            confidence_score=0.74,
            risk_level=RiskLevel.HIGH,
        )


class GitHubActionsRCAAgent(RCAAgent):
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        return RCAResult(
            failure_type=FailureCategory.GITHUB_ACTIONS,
            root_cause="GitHub Actions workflow configuration failed.",
            observed_evidence=_evidence_lines(evidence),
            inference="The issue is likely in workflow YAML, action references, or runner setup.",
            recommended_fix="Update the workflow configuration and re-run CI.",
            files_to_modify=[path for path in evidence.changed_files if path.startswith(".github/workflows/")],
            confidence_score=0.8,
            risk_level=RiskLevel.MEDIUM,
        )


class PythonRCAAgent(RCAAgent):
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        return RCAResult(
            failure_type=FailureCategory.PYTHON_BUILD,
            root_cause="Python build or dependency installation failed.",
            observed_evidence=_evidence_lines(evidence),
            inference="The failure likely comes from dependencies, imports, or syntax.",
            recommended_fix="Update Python source or dependency declarations.",
            files_to_modify=evidence.changed_files,
            confidence_score=0.78,
            risk_level=RiskLevel.MEDIUM,
        )


class UnknownRCAAgent(RCAAgent):
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        return RCAResult(
            failure_type=FailureCategory.UNKNOWN,
            root_cause="The failure category could not be determined from deterministic signals.",
            observed_evidence=_evidence_lines(evidence),
            inference="Manual review or LLM-assisted classification is required.",
            recommended_fix="Collect more targeted evidence before generating a remediation.",
            files_to_modify=[],
            confidence_score=0.2,
            risk_level=RiskLevel.HIGH,
        )
