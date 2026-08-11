from __future__ import annotations

from abc import ABC, abstractmethod

from ai_platform.models.state import EvidenceBundle, RCAResult


class RCAAgent(ABC):
    @abstractmethod
    def analyze(self, evidence: EvidenceBundle) -> RCAResult:
        raise NotImplementedError
