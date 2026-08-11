from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ALLOWED_KINDS = {"ConfigMap", "Deployment", "Service"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_metadata(document: dict[str, Any], path: Path) -> None:
    metadata = document.get("metadata")
    require(isinstance(metadata, dict), f"{path}: metadata must be an object")
    require(isinstance(metadata.get("name"), str), f"{path}: metadata.name is required")


def validate_deployment(document: dict[str, Any], path: Path) -> None:
    spec = document.get("spec")
    require(isinstance(spec, dict), f"{path}: Deployment spec must be an object")
    template = spec.get("template")
    require(isinstance(template, dict), f"{path}: Deployment spec.template is required")
    pod_spec = template.get("spec")
    require(isinstance(pod_spec, dict), f"{path}: Deployment pod spec is required")
    containers = pod_spec.get("containers")
    require(isinstance(containers, list) and containers, f"{path}: containers are required")

    for container in containers:
        require(isinstance(container.get("name"), str), f"{path}: container.name is required")
        require(isinstance(container.get("image"), str), f"{path}: container.image is required")
        require("livenessProbe" in container, f"{path}: livenessProbe is required")
        require("readinessProbe" in container, f"{path}: readinessProbe is required")
        resources = container.get("resources")
        require(isinstance(resources, dict), f"{path}: resources are required")
        require("requests" in resources, f"{path}: resource requests are required")
        require("limits" in resources, f"{path}: resource limits are required")


def validate_service(document: dict[str, Any], path: Path) -> None:
    spec = document.get("spec")
    require(isinstance(spec, dict), f"{path}: Service spec must be an object")
    require(isinstance(spec.get("selector"), dict), f"{path}: Service selector is required")
    ports = spec.get("ports")
    require(isinstance(ports, list) and ports, f"{path}: Service ports are required")


def validate_document(document: Any, path: Path) -> None:
    require(isinstance(document, dict), f"{path}: manifest document must be an object")
    require(isinstance(document.get("apiVersion"), str), f"{path}: apiVersion is required")
    kind = document.get("kind")
    require(kind in ALLOWED_KINDS, f"{path}: unsupported kind {kind!r}")
    validate_metadata(document, path)

    if kind == "Deployment":
        validate_deployment(document, path)
    elif kind == "Service":
        validate_service(document, path)


def main() -> int:
    manifest_paths = sorted(Path("kubernetes").glob("*/*.yaml"))
    require(bool(manifest_paths), "No Kubernetes manifests found")

    for path in manifest_paths:
        documents = list(yaml.safe_load_all(path.read_text()))
        require(bool(documents), f"{path}: empty manifest")
        for document in documents:
            validate_document(document, path)

    print(f"Validated {len(manifest_paths)} Kubernetes manifest files")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
