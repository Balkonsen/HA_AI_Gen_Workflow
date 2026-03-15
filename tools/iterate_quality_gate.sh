#!/usr/bin/env bash
set -euo pipefail

# Iterative quality gate runner for local dev.
# It reruns pre-commit up to MAX_ROUNDS and auto-fixes common environment issues.

MAX_ROUNDS="${1:-3}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [ -x "${ROOT_DIR}/.venv/Scripts/python.exe" ]; then
    PY_CMD=("${ROOT_DIR}/.venv/Scripts/python.exe")
elif command -v python3 >/dev/null 2>&1; then
    PY_CMD=("python3")
elif command -v python >/dev/null 2>&1; then
    PY_CMD=("python")
else
    echo "No Python executable found."
    exit 1
fi

run_precommit() {
    "${PY_CMD[@]}" -m pre_commit run --all-files 2>&1
}

normalize_shell_line_endings() {
    find "${ROOT_DIR}" -type f \( -name "*.sh" -o -name "*.bats" \) \
        ! -path "*/.git/*" ! -path "*/.venv/*" -print0 |
        while IFS= read -r -d '' file; do
            awk '{ sub(/\r$/, ""); print }' "${file}" > "${file}.tmp" && mv "${file}.tmp" "${file}"
        done
}

ensure_precommit_installed() {
    if ! "${PY_CMD[@]}" -m pre_commit --version >/dev/null 2>&1; then
        "${PY_CMD[@]}" -m pip install pre-commit
    fi
}

ensure_hook_prereqs() {
    # Required by Bandit hook environments in some setups.
    "${PY_CMD[@]}" -m pip install pbr >/dev/null 2>&1 || true
}

ensure_precommit_installed

for round in $(seq 1 "${MAX_ROUNDS}"); do
    echo "Round ${round}/${MAX_ROUNDS}: pre-commit --all-files"

    set +e
    output="$(run_precommit)"
    status=$?
    set -e

    echo "${output}"

    if [ ${status} -eq 0 ]; then
        echo "Quality gate passed."
        exit 0
    fi

    handled=0

    if printf '%s' "${output}" | grep -q "No module named pre_commit"; then
        ensure_precommit_installed
        handled=1
    fi

    if printf '%s' "${output}" | grep -q "No module named 'pbr'"; then
        ensure_hook_prereqs
        handled=1
    fi

    if printf '%s' "${output}" | grep -Eq "\\$'\\r'|Literal carriage return|wrong new line character"; then
        normalize_shell_line_endings
        handled=1
    fi

    if [ ${handled} -eq 0 ]; then
        echo "No auto-remediation rule matched. Stop after round ${round}."
        exit ${status}
    fi

done

echo "Quality gate did not pass after ${MAX_ROUNDS} rounds."
exit 1
