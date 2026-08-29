<!-- refreshed: 2026-08-29 -->
# Architecture

**Analysis Date:** 2026-08-29

## System Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Entry Points / Interfaces                    │
│  Shell Script (ha_ai_master_script.sh) │ Python CLI │ Streamlit GUI
│         `ha_ai_master_script.sh`     │ `workflow_orchestrator.py` │ `workflow_gui.py`
└────────────────────────────────────────┬────────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │   WorkflowOrchestrator                   │
                    │   `bin/workflow_orchestrator.py`         │
                    │   - Coordinates full workflow            │
                    │   - Manages state transitions            │
                    │   - Handles error recovery               │
                    └────┬───────┬──────────┬─────────┬────────┘
                         │       │          │         │
        ┌────────────────┼───────┼──────────┼─────────┼─────────────┐
        │                │       │          │         │             │
        ▼                ▼       ▼          ▼         ▼             ▼
    ┌─────────┐  ┌────────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐
    │ Export  │  │ Sanitize   │  │ Generate    │  │ Import   │  │ Validate │  │ Remote    │
    │ Service │  │ Service    │  │ AI Context  │  │ Service  │  │ Service  │  │ Manager   │
    │         │  │            │  │ Service     │  │          │  │          │  │           │
    └────┬────┘  └──┬─────────┘  └──┬────────┘  └──┬───────┘  └──┬───────┘  └──┬────────┘
         │          │               │             │            │            │
         │  ┌───────▼───────────────▼─────────────▼──────────────▼────────────┘
         │  │   Core Services Layer
         │  │   `bin/ha_diagnostic_export.py`     - Export HA configuration
         │  │   `bin/secrets_manager.py`          - Encryption/decryption
         │  │   `bin/ha_ai_context_gen.py`        - AI context generation
         │  │   `bin/ha_config_import.py`         - Configuration import
         │  │   `bin/ha_export_verifier.py`       - Export verification
         │  │   `bin/ssh_transfer.py`             - SSH operations
         │  │   `bin/workflow_config.py`          - Configuration management
         └──┴────────────────────────────────────────────────────────────┘
                                    │
         ┌──────────────────────────┼──────────────────────────┐
         │                          │                          │
         ▼                          ▼                          ▼
    ┌─────────────┐           ┌──────────────┐         ┌─────────────┐
    │ File System │           │ Configuration│         │ SSH/Remote  │
    │ - Exports   │           │ - YAML files │         │ - Paramiko  │
    │ - Secrets   │           │ - Templates  │         │ - Remote HA │
    │ - Context   │           │              │         │             │
    └─────────────┘           └──────────────┘         └─────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| WorkflowOrchestrator | Coordinates complete workflow pipeline, manages state, handles errors | `bin/workflow_orchestrator.py` |
| HAConfigExporter | Exports HA configuration from local or remote, handles file collection | `bin/ha_diagnostic_export.py` |
| SecretsSanitizer | Identifies and removes sensitive data, replaces with labeled placeholders | `bin/secrets_manager.py` |
| SecretsManager | Encrypts/decrypts secrets, manages encryption keys, stores mappings | `bin/secrets_manager.py` |
| HAContextGenerator | Analyzes configuration, generates AI-friendly documentation | `bin/ha_ai_context_gen.py` |
| HAConfigImporter | Imports sanitized configuration back to HA, restores secrets | `bin/ha_config_import.py` |
| ExportVerifier | Validates export structure, checks YAML syntax, verifies entity references | `bin/ha_export_verifier.py` |
| HARemoteManager | Handles SSH connections, transfers files, manages remote operations | `bin/ssh_transfer.py` |
| WorkflowConfig | Loads and manages configuration from YAML, provides defaults | `bin/workflow_config.py` |

## Pattern Overview

**Overall:** Pipeline/Orchestrator pattern with plug-in architecture for services

**Key Characteristics:**
- **Sequential workflow**: Export → Sanitize → Generate → Validate → Import
- **Clear separation of concerns**: Each component has a single responsibility
- **Configuration-driven**: All behavior controlled by YAML configuration
- **Error handling**: Each step can fail independently with recovery options
- **Reversible operations**: Exports and backups allow rollback capability

## Layers

**Presentation Layer:**
- Purpose: User interfaces and entry points
- Location: `bin/workflow_orchestrator.py`, `bin/workflow_gui.py`, `ha_ai_master_script.sh`
- Contains: CLI arguments parsing, GUI forms, shell script command handling
- Depends on: Orchestrator layer
- Used by: End users, CI/CD systems, VS Code tasks

**Orchestration Layer:**
- Purpose: Coordinates workflow stages and manages overall execution flow
- Location: `bin/workflow_orchestrator.py` (WorkflowOrchestrator class)
- Contains: run_full_workflow(), export_from_remote(), import_local(), etc.
- Depends on: Service layer, Configuration layer
- Used by: Presentation layer

**Service Layer:**
- Purpose: Individual workflow services for export, import, validation
- Location: `bin/ha_diagnostic_export.py`, `bin/ha_config_import.py`, `bin/ha_export_verifier.py`, `bin/ha_ai_context_gen.py`
- Contains: Core business logic for each workflow step
- Depends on: Support layer (configuration, secrets, SSH)
- Used by: Orchestration layer

**Support Layer:**
- Purpose: Cross-cutting concerns (configuration, secrets, SSH, validation)
- Location: `bin/workflow_config.py`, `bin/secrets_manager.py`, `bin/ssh_transfer.py`
- Contains: Configuration management, encryption/decryption, SSH operations
- Depends on: External libraries (PyYAML, cryptography, paramiko)
- Used by: Service layer, Orchestration layer

**Integration Layer:**
- Purpose: External system integration (Home Assistant, SSH remotes, file system)
- Location: Various (embedded in service classes)
- Contains: Home Assistant communication, SSH connections, file I/O
- Depends on: External libraries and network/file system
- Used by: Service layer

## Data Flow

### Primary Request Path: Full Workflow Export

1. User invokes workflow via CLI/GUI/shell → WorkflowOrchestrator.run_full_workflow() (`bin/workflow_orchestrator.py:352`)
2. Export phase: HAConfigExporter collects configuration files from source (`bin/ha_diagnostic_export.py:80`)
   - Local: Copy from filesystem via `export_local()` (`bin/workflow_orchestrator.py:92`)
   - Remote: SSH transfer via HARemoteManager.export_config() (`bin/ssh_transfer.py`)
3. Sanitize phase: SecretsSanitizer identifies and replaces sensitive data (`bin/secrets_manager.py`)
   - Detects passwords, tokens, IPs, emails using regex patterns
   - Replaces with labeled placeholders: `<<HA_SECRET_PASSWORD_001>>`
   - Stores actual values encrypted in secrets vault
4. AI Context phase: HAContextGenerator creates AI-friendly documentation (`bin/ha_ai_context_gen.py:46`)
   - Analyzes YAML files using custom loader that handles HA tags (!secret, !include)
   - Extracts entities, devices, automations, integrations
   - Creates markdown context files and prompt suggestions
5. Validation phase: ExportVerifier checks export integrity (`bin/ha_export_verifier.py`)
   - Validates YAML syntax
   - Checks entity_id format and references
   - Verifies secret placeholder consistency
6. Output: 
   - Sanitized config in `exports/export_YYYYMMDD_HHMMSS/config/`
   - AI context in `ai_context/context_YYYYMMDD_HHMMSS/`
   - Encrypted secrets in `secrets/secrets_vault.enc`

### Secondary Flow: Configuration Import

1. User places modified configuration in `imports/` directory
2. User invokes import via CLI → WorkflowOrchestrator.import_local() or import_remote() (`bin/workflow_orchestrator.py:288`)
3. Secret restoration: SecretsManager restores encrypted values in place of placeholders (`bin/secrets_manager.py`)
   - Reads encrypted vault
   - Scans files for placeholder labels
   - Replaces placeholders with actual values
4. Import execution: HAConfigImporter applies configuration (`bin/ha_config_import.py`)
   - Copies files to target HA directory
   - Updates secrets.yaml if needed
   - Creates backup of previous configuration
5. Verification: Validates imported configuration
6. Output: Configuration applied to Home Assistant

### Configuration Loading Flow

1. WorkflowOrchestrator initialization → WorkflowConfig initialization (`bin/workflow_config.py:76`)
2. Config search:
   - Uses explicit path if provided
   - Searches CONFIG_LOCATIONS in order (`bin/workflow_config.py:69`)
   - Falls back to DEFAULT_CONFIG if no file found
3. Path expansion: Resolves home directory and relative paths
4. Usage: Components access via config.get('key.subkey') pattern

**State Management:**
- Minimal state: Each component is largely stateless
- Configuration object passed between components
- Secrets manager maintains in-memory cache of decrypted secrets
- Orchestrator tracks paths and timestamps for workflow stages

## Key Abstractions

**SecretsSanitizer:**
- Purpose: Abstract the identification and replacement of sensitive data
- Examples: `bin/secrets_manager.py` (SecretsSanitizer class)
- Pattern: Visitor pattern - iterates files/fields, sanitizes in-place

**HAYAMLLoader:**
- Purpose: Handle Home Assistant-specific YAML tags gracefully
- Examples: `bin/ha_ai_context_gen.py:15` (custom loader with tag constructors)
- Pattern: Adapter pattern - wraps PyYAML to handle HA extensions

**Workflow Stages:**
- Purpose: Represent discrete, chainable workflow steps
- Examples: export, sanitize, context, validate, import
- Pattern: Pipeline pattern - each stage consumes output of previous

## Entry Points

**Python CLI:**
- Location: `bin/workflow_orchestrator.py`
- Triggers: `python3 bin/workflow_orchestrator.py <command>`
- Responsibilities: Parse arguments, create orchestrator, execute command
- Commands: setup, export, sanitize, context, import, validate, full

**Shell Script:**
- Location: `ha_ai_master_script.sh`
- Triggers: `./ha_ai_master_script.sh <command>`
- Responsibilities: Environment setup, dependency checking, logging, orchestration
- Commands: export, context, import, validate, full

**Streamlit GUI:**
- Location: `bin/workflow_gui.py`
- Triggers: `streamlit run bin/workflow_gui.py`
- Responsibilities: Web UI, interactive workflows, visualization

**Tests Entry:**
- Location: `tests/conftest.py`, `tests/test_*.py`
- Triggers: `pytest` or `python -m pytest`
- Responsibilities: Unit and integration testing

## Architectural Constraints

- **Threading:** Single-threaded event model; no concurrent operations (SSH and file I/O are sequential)
- **Global state:** 
  - WorkflowConfig is created once and passed as reference
  - SecretsManager maintains singleton encryption state per instance
  - No module-level globals except imports
- **Circular imports:** None detected; imports flow unidirectionally through orchestrator
- **SSH dependencies:** SSH operations optional; codebase handles gracefully if paramiko unavailable
- **File permissions:** Encryption key file restricted to 0o600 (Unix only)
- **Configuration:** All runtime behavior determined by YAML config; no hardcoded business logic

## Anti-Patterns

### Mixing Responsibilities in Services

**What happens:** Initial design had some service classes trying to handle both business logic and file I/O

**Why it's wrong:** Makes testing harder, reduces reusability, violates single responsibility principle

**Do this instead:** Create separate service classes for business logic (`HAConfigExporter`, `SecretsSanitizer`) and use dependency injection for file operations. Pattern visible in `bin/workflow_orchestrator.py:100` where HAConfigExporter is instantiated with just output_dir parameter.

### Hardcoded Paths in Components

**What happens:** Some modules used to have hardcoded '/config' paths for HA configuration

**Why it's wrong:** Breaks flexibility for testing, local development, and remote scenarios

**Do this instead:** All path configuration is externalized to WorkflowConfig (`bin/workflow_config.py:18`). Components accept paths as constructor parameters or via config. Example: `bin/workflow_orchestrator.py:86` uses paths from config object.

### Secret Values in Logs

**What happens:** Early logging could accidentally print sensitive values in debug output

**Why it's wrong:** Leaks secrets to log files and CI output

**Do this instead:** Explicitly sanitize before logging. `bin/secrets_manager.py` provides `_mask_value()` method for safe logging. Secrets are never logged; only metadata (counts, labels) are logged.

## Error Handling

**Strategy:** Graceful degradation with detailed error reporting

**Patterns:**
- Try-except blocks in service methods catch specific exceptions
- Errors propagate up with context; orchestrator decides recovery
- YAML parsing errors fall back to raw text extraction (`bin/ha_ai_context_gen.py:61`)
- SSH failures don't block local operations (`bin/workflow_orchestrator.py:71`)
- Validation produces detailed reports rather than boolean pass/fail

## Cross-Cutting Concerns

**Logging:** 
- bash: Color-coded terminal output with `log()`, `info()`, `success()`, `warn()`, `error()` in `ha_ai_master_script.sh`
- Python: Uses print() with status indicators (✓, ✗, ⚠, 🤖); no centralized logger configured

**Validation:** 
- YAML syntax via PyYAML parser
- Entity ID format checking in `bin/ha_export_verifier.py`
- Secret placeholder consistency verification
- Path existence and accessibility checks

**Authentication:** 
- SSH: Key-based (default) or password-based via paramiko (`bin/ssh_transfer.py`)
- Local: File system permissions
- HA API: Token-based (if needed for future enhancements)

---

*Architecture analysis: 2026-08-29*
