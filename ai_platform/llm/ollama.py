from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from ai_platform.models.state import EvidenceBundle, RCAResult


class OllamaRCAEnhancer:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: int = 45,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL") or "http://host.docker.internal:11434").rstrip("/")
        self.model = model or os.getenv("LLM_MODEL") or "qwen2.5:3b"
        self.timeout_seconds = timeout_seconds

    def is_enabled(self) -> bool:
        return (os.getenv("LLM_PROVIDER") or "ollama").lower() == "ollama"

    def enhance(self, rca: RCAResult, evidence: EvidenceBundle) -> RCAResult:
        if not self.is_enabled():
            return rca

        prompt = self._build_prompt(rca, evidence)
        try:
            response = self._generate(prompt)
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return rca

        return RCAResult(
            failure_type=rca.failure_type,
            root_cause=response.get("root_cause") or rca.root_cause,
            observed_evidence=response.get("observed_evidence") or rca.observed_evidence,
            inference=response.get("inference") or rca.inference,
            recommended_fix=response.get("recommended_fix") or rca.recommended_fix,
            files_to_modify=response.get("files_to_modify") or rca.files_to_modify,
            confidence_score=min(float(response.get("confidence_score", rca.confidence_score)), rca.confidence_score),
            risk_level=rca.risk_level,
        )

    def _generate(self, prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode(),
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:  # nosec B310
            data = json.loads(response.read().decode())
        return json.loads(data.get("response") or "{}")

    def _build_prompt(self, rca: RCAResult, evidence: EvidenceBundle) -> str:
        focused_evidence = [
            {
                "source": item.source,
                "kind": item.kind,
                "content": item.content[:3000],
                "metadata": item.metadata,
            }
            for item in evidence.items[:8]
        ]
        return (
            "You are an RCA assistant for a self-healing CI/CD platform. "
            "Use only the observed evidence. Do not invent facts. "
            "Return compact JSON with keys: root_cause, observed_evidence, inference, "
            "recommended_fix, files_to_modify, confidence_score.\n\n"
            f"Deterministic RCA:\n{rca.model_dump_json()}\n\n"
            f"Focused evidence:\n{json.dumps(focused_evidence)}"
        )
