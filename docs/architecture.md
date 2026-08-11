# Architecture

## Scope

This POC demonstrates AI-assisted remediation for CI/CD failures without removing
human approval. The initial milestone is a working delivery path for three FastAPI
services through GitHub Actions, Docker, and Kubernetes. The AI control plane is
layered on top only after that path works.

## Non-Goals For Phase 1

- No Streamlit or custom dashboard.
- No direct production modification.
- No automatic merge.
- No branch protection bypass.
- No vector database.
- No cloud Kubernetes dependency.

## Control Plane Boundary

The GitHub webhook receiver is a trigger only. It validates the webhook signature,
extracts workflow failure metadata, checks duplicate processing, and starts the
LangGraph orchestration. RCA, evidence collection, remediation, verification, and
PR creation live behind separate interfaces.

## Evidence Model

Evidence must be structured JSON before it reaches an RCA agent. Raw logs should
be narrowed to relevant sections and redacted for obvious secrets.

Evidence domains:

- GitHub workflow metadata, failed job, failed step, commit SHA, branch, changed
  files, and focused logs.
- Python tracebacks, dependency errors, requirements, and relevant source files.
- Docker build output, Dockerfile content, and build context hints.
- Security scanner findings including scanner, rule ID, severity, affected file,
  affected package, and recommendation.
- Kubernetes pod status, events, manifests, restart counts, and relevant logs.

## Remediation Boundary

The remediation engine may modify repository files only. It must produce a diff,
pass guardrails, and run verification before a Pull Request is created.

Blocked operations include:

- Deleting infrastructure.
- Modifying GitHub secrets.
- Disabling scanners or tests.
- Removing branch protection.
- Auto-merging PRs.
- Executing unrestricted shell commands.
- Making destructive Kubernetes changes.
- Silently suppressing failing tests.

## Verification Strategy

Verification is selected by touched files and failure category:

- Python changes: Ruff and pytest.
- Docker changes: Docker build and Trivy scan when available.
- Kubernetes changes: manifest validation and kubectl dry-run.
- Security changes: Bandit and scanner-specific checks.
- GitHub Actions changes: YAML parsing and workflow validation where possible.

If verification fails, the incident report records failure details and no PR is
created claiming remediation success.

## Human Approval

GitHub Pull Requests are the review interface. The AI may create a branch, commit
verified changes, and open a PR, but it must not merge or deploy without human
review.
