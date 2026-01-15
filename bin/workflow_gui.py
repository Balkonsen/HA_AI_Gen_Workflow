#!/usr/bin/env python3
"""
HA AI Gen Workflow GUI
Streamlit-based graphical interface for the workflow.
"""

import os
import sys
from pathlib import Path

# Add bin directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import streamlit as st
except ImportError:
    print("Streamlit not installed. Install with: pip install streamlit")
    print("Then run: streamlit run bin/workflow_gui.py")
    sys.exit(1)

from workflow_config import WorkflowConfig
from secrets_manager import SecretsManager
from ssh_transfer import SSHTransfer


def init_session_state():
    """Initialize session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = WorkflowConfig()
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'export_path' not in st.session_state:
        st.session_state.export_path = None
    if 'context_path' not in st.session_state:
        st.session_state.context_path = None


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


def render_configuration():
    """Render configuration page."""
    st.header("⚙️ Configuration")
    st.markdown("Configure your Home Assistant connection and workflow settings.")
    
    config = st.session_state.config
    
    # SSH Configuration
    st.subheader("📡 SSH Connection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ssh_enabled = st.checkbox(
            "Enable SSH for remote HA",
            value=config.get('ssh.enabled', False)
        )
        config.set('ssh.enabled', ssh_enabled)
        
        if ssh_enabled:
            ssh_host = st.text_input(
                "SSH Host",
                value=config.get('ssh.host', ''),
                placeholder="192.168.1.100"
            )
            config.set('ssh.host', ssh_host)
            
            ssh_user = st.text_input(
                "SSH Username",
                value=config.get('ssh.user', 'root')
            )
            config.set('ssh.user', ssh_user)
    
    with col2:
        if ssh_enabled:
            ssh_port = st.number_input(
                "SSH Port",
                value=config.get('ssh.port', 22),
                min_value=1,
                max_value=65535
            )
            config.set('ssh.port', int(ssh_port))
            
            ssh_key = st.text_input(
                "SSH Key Path",
                value=config.get('ssh.key_path', '~/.ssh/id_rsa')
            )
            config.set('ssh.key_path', ssh_key)
            
            remote_path = st.text_input(
                "Remote Config Path",
                value=config.get('ssh.remote_config_path', '/config')
            )
            config.set('ssh.remote_config_path', remote_path)
    
    if ssh_enabled and st.button("🔗 Test SSH Connection"):
        with st.spinner("Testing connection..."):
            ssh = SSHTransfer(
                host=config.get('ssh.host'),
                user=config.get('ssh.user'),
                port=config.get('ssh.port'),
                key_path=config.get('ssh.key_path')
            )
            success, msg = ssh.test_connection()
            
            if success:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")
    
    st.markdown("---")
    
    # Path Configuration
    st.subheader("📁 Local Paths")
    
    col1, col2 = st.columns(2)
    
    with col1:
        export_dir = st.text_input(
            "Export Directory",
            value=config.get('paths.export_dir', './exports')
        )
        config.set('paths.export_dir', export_dir)
        
        secrets_dir = st.text_input(
            "Secrets Directory",
            value=config.get('paths.secrets_dir', './secrets')
        )
        config.set('paths.secrets_dir', secrets_dir)
    
    with col2:
        import_dir = st.text_input(
            "Import Directory",
            value=config.get('paths.import_dir', './imports')
        )
        config.set('paths.import_dir', import_dir)
        
        backup_dir = st.text_input(
            "Backup Directory",
            value=config.get('paths.backup_dir', './backups')
        )
        config.set('paths.backup_dir', backup_dir)
    
    st.markdown("---")
    
    # Secrets Configuration
    st.subheader("🔐 Secrets Encryption")
    
    col1, col2 = st.columns(2)
    
    with col1:
        label_prefix = st.text_input(
            "Secret Label Prefix",
            value=config.get('secrets.label_prefix', 'HA_SECRET')
        )
        config.set('secrets.label_prefix', label_prefix)
    
    with col2:
        auto_restore = st.checkbox(
            "Auto-restore secrets on import",
            value=config.get('secrets.auto_restore', True)
        )
        config.set('secrets.auto_restore', auto_restore)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Save Configuration"):
            config.save('workflow_config.yaml')
            st.success("✅ Configuration saved!")
    
    with col2:
        if st.button("➡️ Next: Export"):
            st.session_state.step = 2
            st.rerun()


def render_export():
    """Render export page."""
    st.header("📤 Export Configuration")
    
    config = st.session_state.config
    
    export_mode = st.radio(
        "Export Mode",
        ["Local", "SSH Remote"],
        horizontal=True
    )
    
    if export_mode == "Local":
        source_path = st.text_input(
            "Home Assistant Config Path",
            value="/config",
            placeholder="/path/to/ha/config"
        )
        
        if st.button("📤 Start Export", type="primary"):
            with st.spinner("Exporting configuration..."):
                from workflow_orchestrator import WorkflowOrchestrator
                
                orchestrator = WorkflowOrchestrator()
                export_path = orchestrator.export_local(source_path)
                
                if export_path:
                    st.session_state.export_path = export_path
                    st.success(f"✅ Export complete: {export_path}")
                else:
                    st.error("❌ Export failed")
    
    else:  # SSH Remote
        if not config.get('ssh.enabled'):
            st.warning("⚠️ SSH not configured. Please configure SSH settings first.")
            if st.button("Go to Configuration"):
                st.session_state.step = 1
                st.rerun()
        else:
            st.info(f"Will export from: {config.get('ssh.user')}@{config.get('ssh.host')}:{config.get('ssh.remote_config_path')}")
            
            if st.button("📤 Start Remote Export", type="primary"):
                with st.spinner("Exporting from remote..."):
                    from workflow_orchestrator import WorkflowOrchestrator
                    
                    orchestrator = WorkflowOrchestrator()
                    export_path = orchestrator.export_from_remote()
                    
                    if export_path:
                        st.session_state.export_path = export_path
                        st.success(f"✅ Export complete: {export_path}")
                    else:
                        st.error("❌ Export failed")
    
    if st.session_state.export_path:
        st.markdown("---")
        st.subheader("🔐 Sanitize Secrets")
        
        if st.button("Sanitize Export"):
            with st.spinner("Sanitizing secrets..."):
                from workflow_orchestrator import WorkflowOrchestrator
                orchestrator = WorkflowOrchestrator()
                orchestrator.sanitize_export(st.session_state.export_path)
                st.success("✅ Secrets sanitized!")
        
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
        placeholder="./exports/export_..."
    )
    
    st.markdown("### Context Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_entities = st.checkbox("Include entity analysis", value=True)
        include_devices = st.checkbox("Include device analysis", value=True)
    
    with col2:
        include_automations = st.checkbox("Include automation analysis", value=True)
        include_integrations = st.checkbox("Include integration analysis", value=True)
    
    if st.button("🤖 Generate AI Context", type="primary"):
        if not export_path:
            st.error("Please specify an export path")
        else:
            with st.spinner("Generating AI context..."):
                from workflow_orchestrator import WorkflowOrchestrator
                
                orchestrator = WorkflowOrchestrator()
                context_path = orchestrator.generate_ai_context(export_path)
                
                if context_path:
                    st.session_state.context_path = context_path
                    st.success(f"✅ AI context generated: {context_path}")
                    
                    # Show generated files
                    st.markdown("### Generated Files")
                    context_dir = Path(context_path)
                    for f in context_dir.iterdir():
                        st.markdown(f"- `{f.name}`")
                else:
                    st.error("❌ Context generation failed")
    
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
        value=config.get('paths.import_dir', './imports'),
        placeholder="./imports/..."
    )
    
    import_mode = st.radio(
        "Import Mode",
        ["Local", "SSH Remote"],
        horizontal=True
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        dry_run = st.checkbox("Dry run (preview only)", value=True)
    
    with col2:
        auto_restore = st.checkbox(
            "Auto-restore secrets",
            value=config.get('secrets.auto_restore', True)
        )
    
    if import_mode == "Local":
        target_path = st.text_input(
            "Target Config Path",
            value="/config",
            placeholder="/path/to/ha/config"
        )
        
        if st.button("📥 Start Import", type="primary"):
            with st.spinner("Importing configuration..."):
                from workflow_orchestrator import WorkflowOrchestrator
                
                orchestrator = WorkflowOrchestrator()
                success = orchestrator.import_local(import_path, target_path, dry_run)
                
                if success:
                    if dry_run:
                        st.success("✅ Dry run complete - no changes made")
                    else:
                        st.success("✅ Import complete!")
                else:
                    st.error("❌ Import failed")
    
    else:  # SSH Remote
        if not config.get('ssh.enabled'):
            st.warning("⚠️ SSH not configured")
        else:
            st.info(f"Will import to: {config.get('ssh.user')}@{config.get('ssh.host')}:{config.get('ssh.remote_config_path')}")
            
            if st.button("📥 Start Remote Import", type="primary"):
                with st.spinner("Importing to remote..."):
                    from workflow_orchestrator import WorkflowOrchestrator
                    
                    orchestrator = WorkflowOrchestrator()
                    success = orchestrator.import_to_remote(import_path, dry_run)
                    
                    if success:
                        st.success("✅ Import complete!")
                    else:
                        st.error("❌ Import failed")
    
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
        placeholder="./exports/export_..."
    )
    
    if st.button("🔍 Run Validation", type="primary"):
        if not validate_path:
            st.error("Please specify a path")
        else:
            with st.spinner("Validating..."):
                from workflow_orchestrator import WorkflowOrchestrator
                
                orchestrator = WorkflowOrchestrator()
                results = orchestrator.validate_export(validate_path)
                
                if results:
                    st.success("✅ Validation complete!")
                    
                    # Display results
                    st.json(results)


def render_full_pipeline():
    """Render full pipeline page."""
    st.header("🚀 Full Pipeline")
    st.markdown("Run the complete workflow in one go.")
    
    config = st.session_state.config
    
    pipeline_mode = st.radio(
        "Mode",
        ["Local", "SSH Remote"],
        horizontal=True
    )
    
    if pipeline_mode == "Local":
        source_path = st.text_input(
            "Home Assistant Config Path",
            value="/config"
        )
    else:
        source_path = config.get('ssh.remote_config_path', '/config')
        st.info(f"Will use remote path: {source_path}")
    
    st.markdown("### Pipeline Steps")
    st.markdown("""
    1. **Export** - Download/copy HA configuration
    2. **Sanitize** - Replace secrets with labels
    3. **AI Context** - Generate context for AI
    4. **Validate** - Verify export completeness
    """)
    
    if st.button("🚀 Run Full Pipeline", type="primary"):
        with st.spinner("Running pipeline..."):
            from workflow_orchestrator import WorkflowOrchestrator
            
            orchestrator = WorkflowOrchestrator()
            mode = "remote" if pipeline_mode == "SSH Remote" else "local"
            success = orchestrator.run_full_workflow(source_path, mode)
            
            if success:
                st.success("✅ Pipeline complete!")
                st.balloons()
            else:
                st.error("❌ Pipeline failed")


def render_settings():
    """Render settings page."""
    st.header("🔧 Settings")
    
    config = st.session_state.config
    
    st.subheader("Export Settings")
    
    include_patterns = st.text_area(
        "Include Patterns (one per line)",
        value="\n".join(config.get('export.include_patterns', []))
    )
    config.set('export.include_patterns', include_patterns.split('\n'))
    
    exclude_patterns = st.text_area(
        "Exclude Patterns (one per line)",
        value="\n".join(config.get('export.exclude_patterns', []))
    )
    config.set('export.exclude_patterns', exclude_patterns.split('\n'))
    
    st.markdown("---")
    
    st.subheader("Sensitive Fields")
    
    sensitive_fields = st.text_area(
        "Sensitive field patterns (one per line)",
        value="\n".join(config.get('export.sensitive_fields', []))
    )
    config.set('export.sensitive_fields', sensitive_fields.split('\n'))
    
    if st.button("💾 Save Settings"):
        config.save('workflow_config.yaml')
        st.success("✅ Settings saved!")


def main():
    """Main entry point."""
    st.set_page_config(
        page_title="HA AI Workflow",
        page_icon="🏠",
        layout="wide"
    )
    
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


if __name__ == "__main__":
    main()
