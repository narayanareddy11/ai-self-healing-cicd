FROM python:3.12-slim

ARG TARGETARCH

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        docker-cli \
        git \
        gnupg \
        unzip \
    && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    arch="${TARGETARCH:-$(dpkg --print-architecture)}"; \
    case "${arch}" in \
      amd64|arm64) ;; \
      *) echo "Unsupported architecture: ${arch}" >&2; exit 1 ;; \
    esac; \
    kubectl_version="$(curl --fail --show-error --location --retry 5 --retry-delay 3 --connect-timeout 10 https://dl.k8s.io/release/stable.txt)"; \
    curl --fail --show-error --location --retry 5 --retry-delay 3 --connect-timeout 10 \
      -o /usr/local/bin/kubectl \
      "https://dl.k8s.io/release/${kubectl_version}/bin/linux/${arch}/kubectl"; \
    chmod +x /usr/local/bin/kubectl

RUN curl --fail --show-error --location --retry 5 --retry-delay 3 --connect-timeout 10 \
      -o /tmp/install-trivy.sh \
      https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh \
    && sh /tmp/install-trivy.sh -b /usr/local/bin \
    && rm -f /tmp/install-trivy.sh

WORKDIR /workspace
