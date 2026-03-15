#!/usr/bin/env python3
"""
HA AI Gen Workflow GUI
Streamlit-based graphical interface for the workflow.
"""

import io
import os
import sys
import contextlib
from pathlib import Path

# Add bin directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Install with: pip install streamlit")
    print("Then run: streamlit run bin/workflow_gui.py")
    sys.exit(1)

from workflow_config import WorkflowConfig  # noqa: E402
from workflow_logger import configure_logger, LogLevel  # noqa: E402
from ssh_transfer import SSHTransfer  # noqa: E402

# Standard HA root directories for path verification
STANDARD_ROOT_DIRS = [
    "/config",
    "/homeassistant",
    "/usr/share/hassio",
    os.path.expanduser("~/.homeassistant"),
    os.path.expanduser("~/homeassistant"),
    os.path.abspath("."),
]


def resolve_and_verify_path(path_str: str) -> tuple:
    """Resolve a path and verify its status.

    Args:
        path_str: The path string to resolve and verify.

    Returns:
        Tuple of (resolved_absolute_path, exists, is_creatable, message)
    """
    if not path_str or not path_str.strip():
        return "", False, False, "Path is empty"

    # Expand user home and environment variables, then resolve to absolute
    expanded = os.path.expanduser(os.path.expandvars(path_str.strip()))
    resolved = os.path.abspath(expanded)

    if os.path.exists(resolved):
        if os.path.isdir(resolved):
            return resolved, True, True, f"✅ Directory exists: {resolved}"
        else:
            return resolved, True, True, f"✅ File exists: {resolved}"

    # Check if parent exists or can be created
    parent = os.path.dirname(resolved)
    if os.path.exists(parent):
        return (
            resolved,
            False,
            True,
            f"⚠️ Does not exist (parent exists, can be created): {resolved}",
        )

    # Walk up to find nearest existing ancestor
    ancestor = parent
    while ancestor and not os.path.exists(ancestor):
        ancestor = os.path.dirname(ancestor)
        if ancestor == os.path.dirname(ancestor):
            break

    if ancestor and os.path.exists(ancestor):
        return (
            resolved,
            False,
            True,
            f"⚠️ Does not exist (nearest ancestor: {ancestor}): {resolved}",
        )

    return (
        resolved,
        False,
        False,
        f"❌ Cannot create — no valid ancestor found: {resolved}",
    )


def find_standard_root() -> str:
    """Find the first available standard HA root directory.

    Returns:
        The first existing standard root directory, or current working directory.
    """
    for root_dir in STANDARD_ROOT_DIRS:
        if os.path.isdir(root_dir):
            return root_dir
    return os.path.abspath(".")


def list_directory_contents(dir_path: str, max_depth: int = 2) -> list:
    """List directory contents up to a given depth.

    Args:
        dir_path: Path to directory.
        max_depth: Maximum depth to recurse (default 2).

    Returns:
        List of (relative_path, is_dir, size) tuples.
    """
    entries = []
    base = Path(dir_path)
    if not base.is_dir():
        return entries

    try:
        for item in sorted(base.iterdir()):
            if item.name.startswith("."):
                continue
            rel = str(item.relative_to(base))
            is_dir = item.is_dir()
            size = item.stat().st_size if item.is_file() else 0
            entries.append((rel, is_dir, size))

            if is_dir and max_depth > 1:
                try:
                    for sub_item in sorted(item.iterdir()):
                        if sub_item.name.startswith("."):
                            continue
                        sub_rel = str(sub_item.relative_to(base))
                        sub_is_dir = sub_item.is_dir()
                        sub_size = sub_item.stat().st_size if sub_item.is_file() else 0
                        entries.append((sub_rel, sub_is_dir, sub_size))
                except PermissionError:
                    entries.append((rel + "/ (permission denied)", True, 0))
    except PermissionError:
        pass

    return entries


def capture_runtime_output(func, *args, **kwargs):
    """Capture stdout/stderr from a function call for terminal display.

    Args:
        func: The callable to execute.
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func.

    Returns:
        Tuple of (result, captured_output_string)
    """
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            stderr_capture.write(f"\nException: {type(e).__name__}: {e}\n")
            result = None

    output = stdout_capture.getvalue()
    errors = stderr_capture.getvalue()
    combined = output
    if errors:
        combined += "\n--- STDERR ---\n" + errors

    return result, combined


def render_terminal_output(output: str, title: str = "Runtime Output"):
    """Render captured output in a terminal-like widget.

    Args:
        output: The output text to display.
        title: Title for the terminal section.
    """
    if not output or not output.strip():
        return

    st.markdown(f"### 🖥️ {title}")
    # Use a dark-themed code block for terminal appearance
    st.code(output, language="log")


def render_path_input_with_validation(label: str, config_key: str, config: WorkflowConfig, key_suffix: str = "") -> str:
    """Render a path input with inline validation status.

    Args:
        label: Display label for the input.
        config_key: Dot-notation config key (e.g., 'paths.export_dir').
        config: WorkflowConfig instance.
        key_suffix: Optional suffix for unique Streamlit widget keys.

    Returns:
        The resolved absolute path string.
    """
    current_value = config.get(config_key, "")
    widget_key = f"path_{config_key}_{key_suffix}" if key_suffix else f"path_{config_key}"

    path_value = st.text_input(label, value=current_value, key=widget_key) or ""

    resolved, exists, creatable, message = resolve_and_verify_path(path_value)

    if path_value:
        if exists:
            st.caption(message)
        elif creatable:
            st.caption(message)
            if st.button(f"📁 Create '{os.path.basename(resolved)}'", key=f"create_{widget_key}"):
                try:
                    Path(resolved).mkdir(parents=True, exist_ok=True)
                    st.success(f"✅ Created: {resolved}")
                    st.rerun()
                except OSError as e:
                    st.error(f"❌ Failed to create directory: {e}")
        else:
            st.caption(message)

        config.set(config_key, resolved)
    else:
        st.caption("⚠️ Path is empty")

    return resolved


def init_session_state():
    """Initialize session state variables."""
    if "config" not in st.session_state:
        st.session_state.config = WorkflowConfig()
    if "step" not in st.session_state:
        st.session_state.step = 1
    if "export_path" not in st.session_state:
        st.session_state.export_path = None
    if "context_path" not in st.session_state:
        st.session_state.context_path = None
    if "log_level" not in st.session_state:
        st.session_state.log_level = "INFO"
    if "runtime_output" not in st.session_state:
        st.session_state.runtime_output = ""
    if "logger" not in st.session_state:
        # Determine base storage path for logs
        export_dir = st.session_state.config.get("paths.export_dir", os.path.abspath("./exports"))
        base_dir = os.path.dirname(export_dir)
        log_file = os.path.join(base_dir, "workflow.log")
        Path(base_dir).mkdir(parents=True, exist_ok=True)
        st.session_state.logger = configure_logger(log_level=st.session_state.log_level, log_file=log_file)


def render_sidebar():
    """Render sidebar with workflow steps."""
    st.sidebar.title("🏠 HA AI Workflow")
    st.sidebar.markdown("---")

    steps = [
        ("1️⃣", "Configuration", 1),
        ("2️⃣", "Export", 2),
        ("3️⃣", "AI Context", 3),
        ("4️⃣", "Import", 4),
        ("5️⃣", "Validate", 5),
    ]

    for icon, name, step_num in steps:
        if st.sidebar.button(f"{icon} {name}", key=f"step_{step_num}"):
            st.session_state.step = step_num

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Actions")

    if st.sidebar.button("🚀 Full Pipeline"):
        st.session_state.step = 6

    if st.sidebar.button("🔧 Settings"):
        st.session_state.step = 7

    if st.sidebar.button("📋 View Logs"):
        st.session_state.step = 8

    if st.sidebar.button("📂 Path Explorer"):
        st.session_state.step = 9

    # Sidebar log level control for quick access
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔊 Verbosity")
    log_level = st.sidebar.selectbox(
        "Log Level",
        ["DEBUG", "VERBOSE", "INFO", "CONDENSED", "WARNING", "ERROR"],
        index=["DEBUG", "VERBOSE", "INFO", "CONDENSED", "WARNING", "ERROR"].index(st.session_state.log_level),
        key="sidebar_log_level",
    )
    if log_level != st.session_state.log_level:
        st.session_state.log_level = log_level
        st.session_state.logger.set_log_level(LogLevel[log_level])
        st.sidebar.caption(f"Log level: {log_level}")

    # CLI hint
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💻 Command Line")
    st.sidebar.code(
        "ha-ai-workflow export\nha-ai-workflow import\nha-ai-workflow status\nha-ai-workflow --help",
        language="bash",
    )


def render_configuration():
    """Render configuration page."""
    st.header("⚙️ Configuration")
    st.markdown("Configure your Home Assistant connection and workflow settings.")

    config = st.session_state.config

    # Detect HA root directory
    ha_root = find_standard_root()
    st.info(f"🏠 Detected HA root: **{ha_root}**")

    # SSH Configuration
    st.subheader("📡 SSH Connection")

    col1, col2 = st.columns(2)

    with col1:
        ssh_enabled = st.checkbox("Enable SSH for remote HA", value=config.get("ssh.enabled", False))
        config.set("ssh.enabled", ssh_enabled)

        if ssh_enabled:
            ssh_host = st.text_input(
                "SSH Host",
                value=config.get("ssh.host", ""),
                placeholder="192.168.1.100",
            )
            config.set("ssh.host", ssh_host)

            ssh_user = st.text_input("SSH Username", value=config.get("ssh.user", "root"))
            config.set("ssh.user", ssh_user)

            # Authentication method selection
            # Determine current auth method: default to "SSH Key"
            current_key = config.get("ssh.key_path", "")
            current_pass = config.get("ssh.password", "")
            default_index = 1 if (current_pass and not current_key) else 0

            auth_method = st.radio(
                "Authentication Method",
                ["SSH Key", "Password"],
                index=default_index,
                horizontal=True,
            )

    with col2:
        if ssh_enabled:
            ssh_port = st.number_input(
                "SSH Port",
                value=config.get("ssh.port", 22),
                min_value=1,
                max_value=65535,
            )
            config.set("ssh.port", int(ssh_port))

            if auth_method == "SSH Key":
                ssh_key = st.text_input("SSH Key Path", value=config.get("ssh.key_path", "~/.ssh/id_rsa"))
                config.set("ssh.key_path", ssh_key)
                config.set("ssh.password", "")  # Clear password if using key
            else:  # Password
                ssh_password = st.text_input(
                    "SSH Password",
                    value=config.get("ssh.password", ""),
                    type="password",
                )
                config.set("ssh.password", ssh_password)
                config.set("ssh.key_path", "")  # Clear key if using password

            remote_path = st.text_input(
                "Remote Config Path",
                value=config.get("ssh.remote_config_path", "/config"),
            )
            config.set("ssh.remote_config_path", remote_path)

    if ssh_enabled and st.button("🔗 Test SSH Connection"):
        with st.spinner("Testing connection..."):
            ssh = SSHTransfer(
                host=config.get("ssh.host"),
                user=config.get("ssh.user"),
                port=config.get("ssh.port"),
                key_path=(config.get("ssh.key_path") if config.get("ssh.key_path") else None),
                password=(config.get("ssh.password") if config.get("ssh.password") else None),
            )
            success, msg = ssh.test_connection()

            if success:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

    st.markdown("---")

    # HA API Token Configuration
    st.subheader("🔑 Home Assistant API Token")
    st.markdown(
        "A **Long-Lived Access Token** enables the workflow to read entities, devices, and add-ons "
        "directly from the HA API — even when `.storage` files are not accessible. "
        "In add-on mode, the `SUPERVISOR_TOKEN` is set automatically."
    )

    current_token = os.environ.get("SUPERVISOR_TOKEN", "")
    token_status = "✅ Token is set" if current_token else "⚠️ No token configured"
    st.caption(token_status)

    ha_token = st.text_input(
        "Long-Lived Access Token",
        value=current_token,
        type="password",
        placeholder="Paste token from HA → Profile → Long-Lived Access Tokens",
        key="ha_api_token",
        help="Generate at: HA → Profile → Security → Long-Lived Access Tokens. "
        "Leave empty in add-on mode (SUPERVISOR_TOKEN is auto-injected).",
    )

    col_token1, col_token2 = st.columns(2)

    with col_token1:
        if ha_token and st.button("🔗 Test API Connection"):
            with st.spinner("Testing HA API..."):
                try:
                    import requests

                    api_url = os.environ.get("HA_API_URL", "http://supervisor/core/api")
                    headers = {
                        "Authorization": f"Bearer {ha_token}",
                        "Content-Type": "application/json",
                    }
                    response = requests.get(f"{api_url}/config", headers=headers, timeout=10)
                    if response.status_code == 200:
                        ha_config = response.json()
                        st.success(f"✅ Connected to HA {ha_config.get('version', 'unknown')}")
                    else:
                        st.error(f"❌ API returned status {response.status_code}")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")

    with col_token2:
        if ha_token and st.button("💾 Save Token"):
            os.environ["SUPERVISOR_TOKEN"] = ha_token
            # Persist to env file for CLI usage
            env_file = os.path.join(os.environ.get("HA_INSTALL_DIR", "/usr/local/ha-ai-workflow"), ".env")
            try:
                # Read existing env file, update SUPERVISOR_TOKEN line
                env_lines = []
                if os.path.exists(env_file):
                    with open(env_file, "r") as f:
                        env_lines = [line for line in f.readlines() if not line.startswith("SUPERVISOR_TOKEN=")]
                env_lines.append(f"SUPERVISOR_TOKEN={ha_token}\n")
                with open(env_file, "w") as f:
                    f.writelines(env_lines)
                os.chmod(env_file, 0o600)
                st.success(f"✅ Token saved to environment and {env_file}")
            except OSError:
                st.warning("⚠️ Token set for this session only (could not write env file)")
                st.info("Token is active for the current session.")

    if ha_token and ha_token != current_token:
        os.environ["SUPERVISOR_TOKEN"] = ha_token

    st.markdown("---")

    # Path Configuration — single base storage path
    st.subheader("📁 Workflow Storage Path")
    st.markdown(
        "Configure the base directory for all workflow data. "
        "Exports, imports, secrets, backups, and logs will be stored in sub-directories here."
    )

    # Derive current base path from export_dir (strip trailing /exports if present)
    current_export = config.get("paths.export_dir", "")
    if current_export.endswith("/exports"):
        default_base = current_export[: -len("/exports")]
    elif current_export.endswith("/ai_exports"):
        default_base = current_export[: -len("/ai_exports")]
    else:
        default_base = os.path.dirname(current_export) if current_export else os.path.abspath("./ha_workflow")

    base_path = st.text_input(
        "Storage Base Path",
        value=default_base,
        placeholder="/config/ai_workflow",
        key="storage_base_path",
        help="All workflow directories (exports, imports, secrets, backups, logs) will be created here.",
    )
    resolved_base, base_exists, base_creatable, base_message = resolve_and_verify_path(base_path)
    st.caption(base_message)

    if resolved_base:
        # Derive and set all sub-paths from the base
        config.set("paths.export_dir", os.path.join(resolved_base, "exports"))
        config.set("paths.import_dir", os.path.join(resolved_base, "imports"))
        config.set("paths.secrets_dir", os.path.join(resolved_base, "secrets"))
        config.set("paths.backup_dir", os.path.join(resolved_base, "backups"))
        config.set("paths.ai_context_dir", os.path.join(resolved_base, "ai_context"))

        # Show derived paths
        with st.expander("📂 Derived sub-directories", expanded=False):
            st.text(f"  Exports:    {os.path.join(resolved_base, 'exports')}")
            st.text(f"  Imports:    {os.path.join(resolved_base, 'imports')}")
            st.text(f"  Secrets:    {os.path.join(resolved_base, 'secrets')}")
            st.text(f"  Backups:    {os.path.join(resolved_base, 'backups')}")
            st.text(f"  AI Context: {os.path.join(resolved_base, 'ai_context')}")
            st.text(f"  Logs:       {os.path.join(resolved_base, 'workflow.log')}")

        if not base_exists and base_creatable:
            if st.button("📁 Create Storage Directory"):
                try:
                    for sub in [
                        "exports",
                        "imports",
                        "secrets",
                        "backups",
                        "ai_context",
                    ]:
                        Path(os.path.join(resolved_base, sub)).mkdir(parents=True, exist_ok=True)
                    st.success(f"✅ Created storage directory: {resolved_base}")
                    st.rerun()
                except OSError as e:
                    st.error(f"❌ Failed to create directory: {e}")

    st.markdown("---")

    # Secrets Configuration
    st.subheader("🔐 Secrets Encryption")

    col1, col2 = st.columns(2)

    with col1:
        label_prefix = st.text_input("Secret Label Prefix", value=config.get("secrets.label_prefix", "HA_SECRET"))
        config.set("secrets.label_prefix", label_prefix)

    with col2:
        auto_restore = st.checkbox(
            "Auto-restore secrets on import",
            value=config.get("secrets.auto_restore", True),
        )
        config.set("secrets.auto_restore", auto_restore)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Save Configuration"):
            config.save("workflow_config.yaml")
            st.success("✅ Configuration saved!")

    with col2:
        if st.button("➡️ Next: Export"):
            st.session_state.step = 2
            st.rerun()


def render_export():
    """Render export page."""
    st.header("📤 Export Configuration")

    config = st.session_state.config

    export_mode = st.radio("Export Mode", ["Local", "SSH Remote"], horizontal=True)

    if export_mode == "Local":
        source_path = st.text_input(
            "Home Assistant Config Path",
            value=find_standard_root(),
            placeholder="/config",
        )
        # Show validation for the source path
        resolved, exists, _creatable, message = resolve_and_verify_path(source_path)
        st.caption(message)

        if st.button("📤 Start Export", type="primary"):
            with st.spinner("Exporting configuration..."):
                from workflow_orchestrator import WorkflowOrchestrator

                orchestrator = WorkflowOrchestrator()
                export_path, output = capture_runtime_output(orchestrator.export_local, source_path)

                st.session_state.runtime_output = output
                if export_path:
                    st.session_state.export_path = export_path
                    st.success(f"✅ Export complete: {export_path}")
                else:
                    st.error("❌ Export failed")

            render_terminal_output(st.session_state.runtime_output)

    else:  # SSH Remote
        if not config.get("ssh.enabled"):
            st.warning("⚠️ SSH not configured. Please configure SSH settings first.")
            if st.button("Go to Configuration"):
                st.session_state.step = 1
                st.rerun()
        else:
            st.info(
                "Will export from: "
                f"{config.get('ssh.user')}@{config.get('ssh.host')}:{config.get('ssh.remote_config_path')}"
            )

            if st.button("📤 Start Remote Export", type="primary"):
                with st.spinner("Exporting from remote..."):
                    from workflow_orchestrator import WorkflowOrchestrator

                    orchestrator = WorkflowOrchestrator()
                    export_path, output = capture_runtime_output(orchestrator.export_from_remote)

                    st.session_state.runtime_output = output
                    if export_path:
                        st.session_state.export_path = export_path
                        st.success(f"✅ Export complete: {export_path}")
                    else:
                        st.error("❌ Export failed")

                render_terminal_output(st.session_state.runtime_output)

    if st.session_state.export_path:
        st.markdown("---")
        st.subheader("🔐 Sanitize Secrets")

        if st.button("Sanitize Export"):
            with st.spinner("Sanitizing secrets..."):
                from workflow_orchestrator import WorkflowOrchestrator

                orchestrator = WorkflowOrchestrator()
                _result, output = capture_runtime_output(orchestrator.sanitize_export, st.session_state.export_path)
                st.session_state.runtime_output = output
                st.success("✅ Secrets sanitized!")

            render_terminal_output(st.session_state.runtime_output)

        col1, col2 = st.columns(2)
        with col2:
            if st.button("➡️ Next: AI Context"):
                st.session_state.step = 3
                st.rerun()


def render_ai_context():
    """Render AI context generation page."""
    st.header("🤖 Generate AI Context")

    export_path = st.text_input(
        "Export Path",
        value=st.session_state.export_path or "",
        placeholder="./exports/export_...",
    )
    if export_path:
        _resolved, _exists, _creatable, message = resolve_and_verify_path(export_path)
        st.caption(message)

    st.markdown("### Context Options")

    col1, col2 = st.columns(2)

    with col1:
        st.checkbox("Include entity analysis", value=True)
        st.checkbox("Include device analysis", value=True)

    with col2:
        st.checkbox("Include automation analysis", value=True)
        st.checkbox("Include integration analysis", value=True)

    if st.button("🤖 Generate AI Context", type="primary"):
        if not export_path:
            st.error("Please specify an export path")
        else:
            with st.spinner("Generating AI context..."):
                from workflow_orchestrator import WorkflowOrchestrator

                orchestrator = WorkflowOrchestrator()
                context_path, output = capture_runtime_output(orchestrator.generate_ai_context, export_path)

                st.session_state.runtime_output = output
                if context_path:
                    st.session_state.context_path = context_path
                    st.success(f"✅ AI context generated: {context_path}")

                    # Show generated files
                    st.markdown("### Generated Files")
                    context_dir = Path(context_path)
                    if context_dir.is_dir():
                        for f in context_dir.iterdir():
                            st.markdown(f"- `{f.name}`")
                else:
                    st.error("❌ Context generation failed")

            render_terminal_output(st.session_state.runtime_output)

    if st.session_state.context_path:
        st.markdown("---")
        st.info("📋 Copy the AI context files to your AI assistant to generate modifications.")

        col1, col2 = st.columns(2)
        with col2:
            if st.button("➡️ Next: Import"):
                st.session_state.step = 4
                st.rerun()


def render_import():
    """Render import page."""
    st.header("📥 Import Configuration")

    config = st.session_state.config

    import_path = st.text_input(
        "Import Path (AI-modified config)",
        value=config.get("paths.import_dir", "./imports"),
        placeholder="./imports/...",
    )
    if import_path:
        _resolved, _exists, _creatable, message = resolve_and_verify_path(import_path)
        st.caption(message)

    import_mode = st.radio("Import Mode", ["Local", "SSH Remote"], horizontal=True)

    col1, col2 = st.columns(2)

    with col1:
        dry_run = st.checkbox("Dry run (preview only)", value=True)

    with col2:
        st.checkbox("Auto-restore secrets", value=config.get("secrets.auto_restore", True))

    if import_mode == "Local":
        target_path = st.text_input("Target Config Path", value=find_standard_root(), placeholder="/config")
        _resolved, _exists, _creatable, message = resolve_and_verify_path(target_path)
        st.caption(message)

        if st.button("📥 Start Import", type="primary"):
            with st.spinner("Importing configuration..."):
                from workflow_orchestrator import WorkflowOrchestrator

                orchestrator = WorkflowOrchestrator()
                success, output = capture_runtime_output(orchestrator.import_local, import_path, target_path, dry_run)

                st.session_state.runtime_output = output
                if success:
                    if dry_run:
                        st.success("✅ Dry run complete - no changes made")
                    else:
                        st.success("✅ Import complete!")
                else:
                    st.error("❌ Import failed")

            render_terminal_output(st.session_state.runtime_output)

    else:  # SSH Remote
        if not config.get("ssh.enabled"):
            st.warning("⚠️ SSH not configured")
        else:
            st.info(
                "Will import to: "
                f"{config.get('ssh.user')}@{config.get('ssh.host')}:{config.get('ssh.remote_config_path')}"
            )

            if st.button("📥 Start Remote Import", type="primary"):
                with st.spinner("Importing to remote..."):
                    from workflow_orchestrator import WorkflowOrchestrator

                    orchestrator = WorkflowOrchestrator()
                    success, output = capture_runtime_output(orchestrator.import_to_remote, import_path, dry_run)

                    st.session_state.runtime_output = output
                    if success:
                        st.success("✅ Import complete!")
                    else:
                        st.error("❌ Import failed")

                render_terminal_output(st.session_state.runtime_output)

    col1, col2 = st.columns(2)
    with col2:
        if st.button("➡️ Next: Validate"):
            st.session_state.step = 5
            st.rerun()


def render_validate():
    """Render validation page."""
    st.header("🔍 Validate Export/Import")

    validate_path = st.text_input(
        "Path to validate",
        value=st.session_state.export_path or "",
        placeholder="./exports/export_...",
    )
    if validate_path:
        _resolved, _exists, _creatable, message = resolve_and_verify_path(validate_path)
        st.caption(message)

    if st.button("🔍 Run Validation", type="primary"):
        if not validate_path:
            st.error("Please specify a path")
        else:
            with st.spinner("Validating..."):
                from workflow_orchestrator import WorkflowOrchestrator

                orchestrator = WorkflowOrchestrator()
                results, output = capture_runtime_output(orchestrator.validate_export, validate_path)

                st.session_state.runtime_output = output
                if results:
                    st.success("✅ Validation complete!")
                    st.json(results)

            render_terminal_output(st.session_state.runtime_output)


def render_full_pipeline():
    """Render full pipeline page."""
    st.header("🚀 Full Pipeline")
    st.markdown("Run the complete workflow in one go.")

    config = st.session_state.config

    pipeline_mode = st.radio("Mode", ["Local", "SSH Remote"], horizontal=True)

    if pipeline_mode == "Local":
        source_path = st.text_input("Home Assistant Config Path", value=find_standard_root())
        _resolved, _exists, _creatable, message = resolve_and_verify_path(source_path)
        st.caption(message)
    else:
        source_path = config.get("ssh.remote_config_path", "/config")
        st.info(f"Will use remote path: {source_path}")

    st.markdown("### Pipeline Steps")
    st.markdown(
        """
    1. **Export** - Download/copy HA configuration
    2. **Sanitize** - Replace secrets with labels
    3. **AI Context** - Generate context for AI
    4. **Validate** - Verify export completeness
    """
    )

    if st.button("🚀 Run Full Pipeline", type="primary"):
        with st.spinner("Running pipeline..."):
            from workflow_orchestrator import WorkflowOrchestrator

            orchestrator = WorkflowOrchestrator()
            mode = "remote" if pipeline_mode == "SSH Remote" else "local"
            success, output = capture_runtime_output(orchestrator.run_full_workflow, source_path, mode)

            st.session_state.runtime_output = output
            if success:
                st.success("✅ Pipeline complete!")
                st.balloons()
            else:
                st.error("❌ Pipeline failed")

        render_terminal_output(st.session_state.runtime_output)


def render_settings():
    """Render settings page."""
    st.header("🔧 Settings")

    config = st.session_state.config

    st.subheader("Export Settings")

    include_patterns = st.text_area(
        "Include Patterns (one per line)",
        value="\n".join(config.get("export.include_patterns", [])),
    )
    config.set("export.include_patterns", include_patterns.split("\n"))

    exclude_patterns = st.text_area(
        "Exclude Patterns (one per line)",
        value="\n".join(config.get("export.exclude_patterns", [])),
    )
    config.set("export.exclude_patterns", exclude_patterns.split("\n"))

    st.markdown("---")

    st.subheader("Sensitive Fields")

    sensitive_fields = st.text_area(
        "Sensitive field patterns (one per line)",
        value="\n".join(config.get("export.sensitive_fields", [])),
    )
    config.set("export.sensitive_fields", sensitive_fields.split("\n"))

    if st.button("💾 Save Settings"):
        config.save("workflow_config.yaml")
        st.success("✅ Settings saved!")


def render_logs():
    """Render log viewer page."""
    st.header("📋 Workflow Logs")
    st.markdown("View and manage workflow logs with different verbosity levels.")

    # Log level selector
    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "VERBOSE", "INFO", "CONDENSED", "WARNING", "ERROR", "CRITICAL"],
            index=2,  # Default to INFO
            help="Select the minimum log level to display",
        )

        if log_level != st.session_state.log_level:
            st.session_state.log_level = log_level
            st.session_state.logger.set_log_level(LogLevel[log_level])

    with col2:
        export_dir = st.session_state.config.get("paths.export_dir", os.path.abspath("./exports"))
        log_dir = os.path.dirname(export_dir)
        log_file = st.text_input("Log File Path", value=os.path.join(log_dir, "workflow.log"))

    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh"):
            st.rerun()

    st.markdown("---")

    # Display log file
    if Path(log_file).exists():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader("Log Contents")

        with col2:
            num_lines = st.number_input("Show last N lines", min_value=10, max_value=1000, value=100, step=10)

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Show last N lines
            last_lines = lines[-num_lines:] if len(lines) > num_lines else lines

            # Display in code block
            log_content = "".join(last_lines)
            st.code(log_content, language="log")

            # Stats
            st.info(f"📊 Total lines: {len(lines)} | Showing: {len(last_lines)}")

            # Download button
            st.download_button(
                label="⬇️ Download Full Log",
                data="".join(lines),
                file_name="workflow.log",
                mime="text/plain",
            )

        except Exception as e:
            st.error(f"❌ Error reading log file: {e}")
    else:
        st.warning(f"⚠️ Log file not found: {log_file}")
        st.info("Run a workflow operation to generate logs.")

    st.markdown("---")

    # Diagnostic report generator
    st.subheader("🔍 Diagnostic Report")
    st.markdown("Generate a diagnostic report for troubleshooting issues.")

    col1, col2 = st.columns([2, 1])

    with col1:
        report_path = st.text_input(
            "Report Output Path",
            value=os.path.join(log_dir, f"diagnostic_report_{Path(log_file).stem}.md"),
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📄 Generate Report"):
            try:
                with st.spinner("Generating diagnostic report..."):
                    output = st.session_state.logger.create_diagnostic_report(
                        output_path=report_path, include_context=True
                    )
                st.success(f"✅ Diagnostic report created: {output}")

                # Show preview
                if Path(output).exists():
                    with open(output, "r", encoding="utf-8") as f:
                        preview = f.read()
                    with st.expander("📄 Report Preview"):
                        st.markdown(preview)
            except Exception as e:
                st.error(f"❌ Error generating report: {e}")

    st.markdown("---")

    # Clear logs option
    st.subheader("🗑️ Log Management")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Clear Log File", type="secondary"):
            if Path(log_file).exists():
                try:
                    with open(log_file, "w") as f:
                        f.write("")
                    st.success("✅ Log file cleared")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error clearing log: {e}")
            else:
                st.warning("⚠️ Log file does not exist")

    with col2:
        if st.button("📁 Open Log Directory", type="secondary"):
            st.info(f"📂 Log directory: {log_dir}")
            try:
                # List files in log directory
                log_path = Path(log_dir)
                if log_path.exists():
                    files = list(log_path.glob("*.log"))
                    if files:
                        st.write("Available log files:")
                        for file in files:
                            st.write(f"  - {file.name}")
                    else:
                        st.write("No log files found")
            except Exception as e:
                st.error(f"Error: {e}")


def render_path_explorer():
    """Render a file explorer for HA installation directories."""
    st.header("📂 HA Path Explorer")
    st.markdown(
        "Browse and configure directories inside your Home Assistant installation. "
        "Use this to verify paths exist and to create missing workflow directories."
    )

    config = st.session_state.config

    # Detect and show HA root
    ha_root = find_standard_root()

    st.subheader("🏠 HA Installation Root")
    available_roots = [d for d in STANDARD_ROOT_DIRS if os.path.isdir(d)]
    if available_roots:
        ha_root = st.selectbox(
            "Detected HA root directories",
            available_roots,
            index=0,
            help="Standard HA directories found on this system",
        )
        st.success(f"✅ Using HA root: {ha_root}")
    else:
        ha_root = st.text_input(
            "HA root directory (none auto-detected)",
            value=os.path.abspath("."),
        )
        st.warning("⚠️ No standard HA root directory found. Using current directory.")

    st.markdown("---")

    # Directory browser
    st.subheader("📁 Directory Browser")
    browse_path = st.text_input("Browse path", value=ha_root, key="explorer_browse_path")

    resolved, exists, _creatable, message = resolve_and_verify_path(browse_path)
    st.caption(message)

    if exists and os.path.isdir(resolved):
        entries = list_directory_contents(resolved)
        if entries:
            for rel_path, is_dir, size in entries:
                icon = "📁" if is_dir else "📄"
                depth = rel_path.count(os.sep)
                indent = "　" * depth  # Use ideographic space for indentation
                size_str = f" ({size:,} bytes)" if not is_dir and size > 0 else ""
                st.text(f"{indent}{icon} {rel_path}{size_str}")
        else:
            st.info("📭 Directory is empty")
    elif exists:
        st.info(f"📄 {resolved} is a file, not a directory")

    st.markdown("---")

    # Workflow directory status overview
    st.subheader("📋 Workflow Directory Status")
    st.markdown("Overview of all configured workflow directories and their status.")

    path_configs = [
        ("Export Directory", "paths.export_dir"),
        ("Import Directory", "paths.import_dir"),
        ("Secrets Directory", "paths.secrets_dir"),
        ("Backup Directory", "paths.backup_dir"),
        ("AI Context Directory", "paths.ai_context_dir"),
    ]

    all_exist = True
    missing_dirs = []

    for label, key in path_configs:
        path_val = config.get(key, "")
        resolved, exists, creatable, _msg = resolve_and_verify_path(path_val)

        if exists:
            st.text(f"  ✅ {label}: {resolved}")
        elif creatable:
            st.text(f"  ⚠️ {label}: {resolved} (missing, can be created)")
            all_exist = False
            missing_dirs.append((label, resolved))
        else:
            st.text(f"  ❌ {label}: {resolved} (cannot create)")
            all_exist = False

    if all_exist:
        st.success("✅ All workflow directories exist and are ready.")
    elif missing_dirs:
        st.warning(f"⚠️ {len(missing_dirs)} director(y/ies) missing.")
        if st.button("📁 Create All Missing Directories"):
            created = 0
            for label, dir_path in missing_dirs:
                try:
                    Path(dir_path).mkdir(parents=True, exist_ok=True)
                    st.success(f"✅ Created: {label} → {dir_path}")
                    created += 1
                except OSError as e:
                    st.error(f"❌ Failed to create {label}: {e}")
            if created > 0:
                st.rerun()


def main():
    """Main entry point."""
    st.set_page_config(page_title="HA AI Workflow", page_icon="🏠", layout="wide")

    init_session_state()
    render_sidebar()

    # Render current step
    step = st.session_state.step

    if step == 1:
        render_configuration()
    elif step == 2:
        render_export()
    elif step == 3:
        render_ai_context()
    elif step == 4:
        render_import()
    elif step == 5:
        render_validate()
    elif step == 6:
        render_full_pipeline()
    elif step == 7:
        render_settings()
    elif step == 8:
        render_logs()
    elif step == 9:
        render_path_explorer()


if __name__ == "__main__":
    main()
