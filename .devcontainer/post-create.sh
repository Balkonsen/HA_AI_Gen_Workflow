#!/usr/bin/env bash
set -euo pipefail

# Install missing base tools only when needed to keep rebuilds faster.
missing_pkgs=""
for pkg in jq make git shellcheck; do
  if ! command -v "$pkg" >/dev/null 2>&1; then
    missing_pkgs="$missing_pkgs $pkg"
  fi
done

if [ -n "$missing_pkgs" ]; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends $missing_pkgs
fi

python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements-test.txt pre-commit

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pre-commit install || echo "Skipping pre-commit install: unable to install hooks in current workspace"
else
  echo "Skipping pre-commit install: workspace is not a git worktree"
fi
