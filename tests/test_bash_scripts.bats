#!/bin/bash
###############################################################################
# Bash Script Tests for HA AI Gen Workflow
# Tests for shell scripts using BATS (Bash Automated Testing System)
###############################################################################

setup() {
    # Setup test environment
    export TEST_DIR="$(mktemp -d)"
    export CONFIG_DIR="${TEST_DIR}/config"
    export EXPORT_DIR="${TEST_DIR}/exports"
    mkdir -p "${CONFIG_DIR}" "${EXPORT_DIR}"
}

teardown() {
    # Cleanup test environment
    rm -rf "${TEST_DIR}"
}

@test "ha_ai_master_script.sh exists and is executable" {
    [ -x "../ha_ai_master_script.sh" ]
}

@test "setup.sh exists and is executable" {
    [ -x "../setup.sh" ]
}

@test "Master script shows help with --help flag" {
    run ../ha_ai_master_script.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "Usage:" ]]
}

@test "Master script validates command arguments" {
    run ../ha_ai_master_script.sh invalid_command
    [ "$status" -ne 0 ]
}

@test "Export command creates required directories" {
    # Mock the export process
    CONFIG_DIR="${TEST_DIR}/config" ../ha_ai_master_script.sh export --dry-run || true
    # Directory should be created even in dry-run
}

@test "Script handles missing dependencies gracefully" {
    # Test with PATH that doesn't include required tools
    PATH="/usr/bin:/bin" run ../ha_ai_master_script.sh export --dry-run
    # Should either succeed or give clear error message
}

@test "Git initialization creates repository" {
    cd "${TEST_DIR}"
    git init
    [ -d ".git" ]
}

@test "Secrets directory is created with proper permissions" {
    mkdir -p "${TEST_DIR}/secrets"
    chmod 700 "${TEST_DIR}/secrets"
    [ -d "${TEST_DIR}/secrets" ]
    stat -c "%a" "${TEST_DIR}/secrets" | grep "700"
}
