#!/usr/bin/env bash
set -euo pipefail

# Installs kubectl for the current user (no sudo) into ~/.local/bin.
# This is the safest default for partner laptops and WSL.

VERSION="${VERSION:-}"
OS="${OS:-linux}"
ARCH="${ARCH:-amd64}"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/install-kubectl.sh [--version vX.Y.Z]

Defaults:
  - Installs the Kubernetes upstream "stable" kubectl for linux/amd64
  - Installs to: ~/.local/bin/kubectl (no sudo)

Options:
  --version vX.Y.Z   Install a specific version (example: v1.30.8)

Notes:
  - Your shell must have ~/.local/bin in PATH (this repo assumes that).
EOF
}

fail() { echo "FAIL: $*" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) fail "unknown arg: $1 (use --help)" ;;
  esac
done

if ! have curl && ! have wget; then
  fail "need curl or wget"
fi
if ! have sha256sum; then
  fail "need sha256sum"
fi

fetch() {
  local url="$1"
  if have curl; then
    curl -fsSL "$url"
  else
    wget -qO- "$url"
  fi
}

if [[ -z "${VERSION}" ]]; then
  VERSION="$(fetch "https://dl.k8s.io/release/stable.txt")"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

echo "Installing kubectl ${VERSION}..."

bin_url="https://dl.k8s.io/release/${VERSION}/bin/${OS}/${ARCH}/kubectl"
sha_url="${bin_url}.sha256"

if have curl; then
  curl -fsSLo "${tmp}/kubectl" "${bin_url}"
  curl -fsSLo "${tmp}/kubectl.sha256" "${sha_url}"
else
  wget -qO "${tmp}/kubectl" "${bin_url}"
  wget -qO "${tmp}/kubectl.sha256" "${sha_url}"
fi

(cd "$tmp" && echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check) >/dev/null

mkdir -p "${HOME}/.local/bin"
install -m 0755 "${tmp}/kubectl" "${HOME}/.local/bin/kubectl"

echo "OK: $(command -v kubectl || true)"
kubectl version --client

