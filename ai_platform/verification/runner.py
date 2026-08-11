from __future__ import annotations

import subprocess  # nosec B404
import sys
from collections.abc import Sequence

from ai_platform.models.state import VerificationResult, VerificationStatus

ALLOWED_COMMANDS = {
    "python -m ruff check services ai_platform tests scripts",
    "python -m pytest",
    "python scripts/validate-kubernetes-manifests.py",
    "docker build -t ai-user-service:local services/user-service",
    "docker build -t ai-product-service:local services/product-service",
    "docker build -t ai-order-service:local services/order-service",
}


class VerificationRunner:
    def __init__(self, cwd: str = ".") -> None:
        self.cwd = cwd

    def run(self, commands: Sequence[str]) -> VerificationResult:
        if not commands:
            return VerificationResult(status=VerificationStatus.SKIPPED, output="No commands requested")

        output: list[str] = []
        for command in commands:
            if command not in ALLOWED_COMMANDS:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    commands=list(commands),
                    output=f"Command is not allowlisted: {command}",
                )
            argv = command.split()
            if argv[0] == "python":
                argv[0] = sys.executable
            completed = subprocess.run(
                argv,
                cwd=self.cwd,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )  # nosec B603
            output.append(completed.stdout)
            output.append(completed.stderr)
            if completed.returncode != 0:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    commands=list(commands),
                    output="\n".join(output),
                )

        return VerificationResult(
            status=VerificationStatus.PASSED,
            commands=list(commands),
            output="\n".join(output),
        )
