"""
Wealth Advisor Assistant - Streamlit UI

Refactored compact layout with:
- No sidebar, compact horizontal header
- 3-column grid layout
- Minimal, focused data display
"""

import streamlit as st
import json
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from main import run_analysis
from memory.memory_store import memory_store
from utils.llm_client import get_llm


def render_compact_header():
    """Render compact header with client selection and actions"""
    header_col1, header_col2, header_col3, header_col4, header_col5 = st.columns([1.5, 1.5, 1, 1, 1])

    client_id = None
    with header_col1:
        client_id = st.selectbox(
            "Client",
            options=["C-12345", "C-67890"],
            key="client_select",
            label_visibility="collapsed"
        )

    with header_col2:
        try:
            llm = get_llm(temperature=0.5)
            st.success("🟢 LLM Ready")
        except:
            st.error("🔴 LLM Offline")

    with header_col3:
        st.caption(f"Model: {os.getenv('LLM_MODEL', 'gpt-4-mini')[:15]}")

    with header_col4:
        if st.button("⚙️", help="Settings", key="settings_btn"):
            st.session_state.show_settings = not st.session_state.get("show_settings", False)

    with header_col5:
        if st.button("📚", help="Help", key="help_btn"):
            st.session_state.show_help = not st.session_state.get("show_help", False)

    return client_id


def render_action_buttons():
    """Render action buttons in compact horizontal layout"""
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([2, 1.5, 1.2, 1.2])

    with btn_col1:
        if st.button("▶️ Run Analysis", type="primary", use_container_width=True, key="run_btn"):
            return "run"

    with btn_col2:
        if st.button("📊 History", use_container_width=True, key="history_btn"):
            return "history"

    with btn_col3:
        if st.button("💾 Export", use_container_width=True, key="export_btn"):
            return "export"

    with btn_col4:
        if st.button("🔄 Clear", use_container_width=True, key="clear_btn"):
            return "clear"

    return None


def render_metrics_cards(analysis):
    """Render key metrics in compact cards"""
    m_col1, m_col2, m_col3 = st.columns(3)

    with m_col1:
        net_worth = analysis.get("net_worth", 0)
        st.metric(
            "Net Worth",
            f"${net_worth:,.0f}",
            delta="Stable" if net_worth > 200000 else "Monitor"
        )

    with m_col2:
        risk = analysis.get("risk_profile", "unknown").title()
        risk_emoji = {"Conservative": "🛡️", "Moderate": "⚖️", "Aggressive": "🚀"}.get(risk, "❓")
        st.metric("Risk Profile", f"{risk_emoji} {risk}")

    with m_col3:
        confidence = analysis.get("confidence_score", 0)
        st.metric("Confidence", f"{int(confidence * 100)}%", delta="High" if confidence > 0.8 else "Fair")


def render_anomalies_section(analysis):
    """Render anomalies in compact format"""
    anomalies = analysis.get("anomalies", [])

    if not anomalies:
        st.success("✅ No anomalies detected - Financial health is stable")
    else:
        for anomaly in anomalies:
            severity = anomaly.get("severity", "low").upper()
            severity_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚪")
            st.warning(f"{severity_emoji} **{anomaly.get('anomaly_type')}** - {severity}")
            st.caption(anomaly.get("description"))


def render_recommendations_section(analysis):
    """Render recommendations with LLM indicators"""
    recommendations = analysis.get("recommendations", [])
    llm_recommendations = analysis.get("llm_recommendations", [])

    # Parse recommendations (handle both strings and sections)
    rec_display = []
    for rec in recommendations:
        if rec and rec.strip() and not rec.endswith(":"):
            rec_display.append(rec)

    # Display with badges
    for i, rec in enumerate(rec_display, 1):
        is_llm = rec in llm_recommendations
        badge = "🤖" if is_llm else "📋"

        # Truncate long recommendations
        display_text = rec[:100] + "..." if len(rec) > 100 else rec
        st.write(f"{badge} **{i}.** {display_text}")

    # Show AI enhancement indicator
    if analysis.get("llm_enhanced"):
        st.info("✨ Analysis enhanced with AI recommendations")


def render_summary_panel(analysis):
    """Render LLM summary in a compact panel"""
    summary = analysis.get("llm_summary", "No summary available")

    # Display in a compact way
    with st.container(border=True):
        st.write(summary)


def render_approval_section(result):
    """Render human approval UI in compact format"""
    if not result.get("requires_approval"):
        return

    if result.get("approval_status") == "pending":
        st.divider()
        st.warning("⚠️ **Approval Required**")

        # Get high-severity anomalies
        analysis = result.get("analysis_result", {})
        anomalies = analysis.get("anomalies", [])
        high_severity = [a for a in anomalies if a.get("severity") == "high"]

        if high_severity:
            st.write(f"**{len(high_severity)} high-severity issue(s) detected:**")
            for a in high_severity:
                st.caption(f"🔴 {a.get('anomaly_type')}: {a.get('description')}")

        # Approval buttons
        approval_col1, approval_col2, approval_col3 = st.columns([2, 1, 1])

        with approval_col2:
            if st.button("✅ Approve", type="primary", use_container_width=True, key="approve_final"):
                result["approval_status"] = "approved"
                result["logs"] = result.get("logs", []) + ["Approved via UI"]
                st.session_state.last_result = result
                st.rerun()

        with approval_col3:
            if st.button("❌ Reject", use_container_width=True, key="reject_final"):
                result["approval_status"] = "rejected"
                result["logs"] = result.get("logs", []) + ["Rejected via UI"]
                st.session_state.last_result = result
                st.rerun()

    elif result.get("approval_status") == "approved":
        st.divider()
        st.success("✅ **Analysis Approved** - Ready for implementation")

    elif result.get("approval_status") == "rejected":
        st.divider()
        st.error("❌ **Analysis Rejected** - Flagged for manual review")


def render_workflow_status():
    """Render compact workflow status"""
    col1, col2, col3 = st.columns(3)

    analysis_done = st.session_state.get("analysis_completed", False)
    requires_approval = (st.session_state.get("last_result") or {}).get("requires_approval", False)
    approval_status = (st.session_state.get("last_result") or {}).get("approval_status", "pending")

    with col1:
        status = "✅" if analysis_done else "⏳"
        st.metric("Data Fetch", status)

    with col2:
        status = "✅" if analysis_done else "⏳"
        st.metric("Analysis", status)

    with col3:
        if requires_approval:
            status = "⚠️" if approval_status == "pending" else ("✅" if approval_status == "approved" else "❌")
        else:
            status = "✅" if analysis_done else "⏳"
        st.metric("Approval", status)


def render_memory_section(client_id):
    """Render memory and history in a collapsible section"""
    with st.expander("🧠 Memory & History", expanded=False):
        mem_tab1, mem_tab2 = st.tabs(["Session Memory", "Client History"])

        with mem_tab1:
            summary = memory_store.get_session_summary()
            if summary:
                st.text_area(
                    "Memory Summary",
                    summary[:500] + "..." if len(summary) > 500 else summary,
                    height=120,
                    disabled=True,
                    label_visibility="collapsed"
                )
            else:
                st.caption("No session memory yet")

        with mem_tab2:
            history = memory_store.get_client_history(client_id)
            if history:
                for entry in history:
                    st.caption(f"📅 {entry.get('timestamp')}")
                    st.write(entry.get('llm_summary', 'No summary'))
            else:
                st.caption("No history available")


def render_execution_logs(result):
    """Render execution logs in a collapsible section"""
    with st.expander("📋 Execution Logs", expanded=False):
        logs = result.get("logs", [])
        if logs:
            for log in logs:
                st.caption(f"• {log}")
        else:
            st.caption("No logs available")


def apply_compact_styling():
    """Apply CSS for compact layout"""
    st.markdown("""
        <style>
            /* Reduce vertical spacing */
            [data-testid="stVerticalBlock"] > [style*="flex-direction: column"] > [data-testid="stVerticalBlock"] {
                margin-top: -0.5rem;
            }

            /* Compact metrics */
            [data-testid="metric-container"] {
                padding: 0.3rem 0.5rem;
            }

            /* Compact selectbox */
            [data-testid="stSelectbox"] {
                margin-top: -0.5rem;
            }

            /* Reduce section spacing */
            .st-emotion-cache-16idsys {
                padding: 0.5rem 0;
            }

            /* Minimal divider spacing */
            hr {
                margin: 0.5rem 0;
            }

            /* Compact button styling */
            button {
                padding: 0.25rem 0.75rem;
                font-size: 0.9rem;
            }

            /* Reduce caption margin */
            .st-emotion-cache-1jicfl2 {
                margin-top: -0.5rem;
            }
        </style>
    """, unsafe_allow_html=True)


def main():
    # Page config - hide sidebar completely
    st.set_page_config(
        page_title="Wealth Advisor",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="collapsed",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )

    # Apply compact styling
    apply_compact_styling()

    # Title
    st.title("💰 Wealth Advisor Assistant")
    st.caption("Multi-Agent System with LLM Enhancement")

    # HEADER SECTION - Client selection & status
    st.markdown("---")
    client_id = render_compact_header()

    # ACTION BUTTONS
    st.markdown("")
    action = render_action_buttons()

    if action == "clear":
        st.session_state.analysis_completed = False
        st.session_state.last_result = None
        st.rerun()

    # Handle history action - display history in an expander
    if action == "history":
        history = memory_store.get_client_history(client_id)
        if history:
            with st.expander("📜 Client History", expanded=True):
                for i, entry in enumerate(history):
                    st.markdown(f"**Entry {i+1}** - 📅 {entry.get('timestamp', 'Unknown')}")
                    st.write(entry.get('llm_summary', 'No summary available'))
                    if entry.get('analysis_data'):
                        with st.expander("View Analysis Details"):
                            st.json(entry.get('analysis_data'))
                    st.divider()
        else:
            st.info("No history available for this client")

    # MAIN CONTENT AREA
    st.markdown("")

    # Check if we need to run analysis
    if action == "run" or st.session_state.get("pending_analysis"):
        with st.spinner("⏳ Running analysis..."):
            result = run_analysis(client_id)
            st.session_state.last_result = result
            st.session_state.analysis_completed = True
            st.session_state.pending_analysis = False
            # Store in memory
            analysis = result.get("analysis_result", {})
            if analysis:
                memory_store.store_analysis(client_id, analysis)

    # DISPLAY RESULTS
    if st.session_state.get("analysis_completed"):
        result = st.session_state.get("last_result")
        analysis = result.get("analysis_result", {})

        if analysis:
            # 3-COLUMN MAIN LAYOUT
            col_main1, col_main2, col_main3 = st.columns([1.2, 1.2, 1.4])

            with col_main1:
                st.markdown("### 📊 Key Metrics")
                render_metrics_cards(analysis)

            with col_main2:
                st.markdown("### ⚠️ Anomalies")
                render_anomalies_section(analysis)

            with col_main3:
                st.markdown("### 💡 Recommendations")
                render_recommendations_section(analysis)

            # SUMMARY SECTION
            st.divider()
            render_summary_panel(analysis)

            # WORKFLOW STATUS
            st.markdown("")
            st.markdown("---")
            render_workflow_status()

            # APPROVAL SECTION (if needed)
            render_approval_section(result)

            # MEMORY & EXECUTION LOGS (collapsed)
            st.markdown("")
            col_lower1, col_lower2 = st.columns(2)

            with col_lower1:
                render_memory_section(client_id)

            with col_lower2:
                render_execution_logs(result)

        else:
            st.error("❌ No analysis results available")
            if result.get("errors"):
                st.write("Errors:", result.get("errors"))

    else:
        # Initial state - show placeholder
        st.info("👈 Select a client and click **Run Analysis** to get started")

    # FOOTER
    st.markdown("---")
    st.caption("Wealth Advisor Assistant v2.0 - Compact & Efficient")


if __name__ == "__main__":
    # Initialize session state
    if "analysis_completed" not in st.session_state:
        st.session_state.analysis_completed = False
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = False
    if "show_help" not in st.session_state:
        st.session_state.show_help = False
    if "pending_analysis" not in st.session_state:
        st.session_state.pending_analysis = False

    main()