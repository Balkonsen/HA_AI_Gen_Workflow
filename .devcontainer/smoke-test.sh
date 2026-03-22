#!/usr/bin/env bash
set -euo pipefail

printf "\n[devcontainer] Running smoke checks...\n\n"

check_cmd() {
  local name="$1"
  local cmd="$2"
  printf -- "- %-34s" "$name"
  if eval "$cmd" >/dev/null 2>&1; then
    printf "OK\n"
  else
    printf "FAIL\n"
    return 1
  fi
}

check_cmd "python available" "python --version"
check_cmd "python3 available" "python3 --version"
check_cmd "pip available" "python -m pip --version"
check_cmd "bash available" "bash --version"
check_cmd "make available" "make --version"
check_cmd "git available" "git --version"
check_cmd "jq available" "jq --version"
check_cmd "shellcheck available" "shellcheck --version"
check_cmd "docker available" "docker --version"

printf -- "- %-34s" "python deps import check"
python - <<'PY'
import cryptography
import paramiko
import requests
import streamlit
import yaml
import pytest
print("ok")
PY
printf "OK\n"

printf "\n[devcontainer] Smoke checks passed.\n"
