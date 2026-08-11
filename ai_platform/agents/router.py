from __future__ import annotations

from ai_platform.agents.base import RCAAgent
from ai_platform.agents.specialists import (
    DockerRCAAgent,
    GitHubActionsRCAAgent,
    KubernetesRCAAgent,
    PythonRCAAgent,
    SecurityRCAAgent,
    TestRCAAgent,
    UnknownRCAAgent,
)
from ai_platform.models.state import FailureCategory


class RCAAgentRouter:
    def __init__(self) -> None:
        self._agents: dict[FailureCategory, RCAAgent] = {
            FailureCategory.PYTHON_BUILD: PythonRCAAgent(),
            FailureCategory.UNIT_TEST: TestRCAAgent(),
            FailureCategory.SECURITY: SecurityRCAAgent(),
            FailureCategory.DOCKER: DockerRCAAgent(),
            FailureCategory.KUBERNETES: KubernetesRCAAgent(),
            FailureCategory.GITHUB_ACTIONS: GitHubActionsRCAAgent(),
            FailureCategory.UNKNOWN: UnknownRCAAgent(),
        }

    def select(self, category: FailureCategory) -> RCAAgent:
        return self._agents.get(category, self._agents[FailureCategory.UNKNOWN])
