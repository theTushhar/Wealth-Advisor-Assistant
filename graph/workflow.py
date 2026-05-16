"""LangGraph workflow definition with nodes and edges."""

from langgraph.graph import StateGraph, END
from typing import Dict, Any
import logging

from agents.fetcher_node import fetcher_node
from agents.analyzer_node import analyzer_node
from state.agent_state import AgentState
from memory.memory_store import memory_store

logger = logging.getLogger(__name__)

# Try to import LLM client - graceful fallback
try:
    from utils.llm_client import generate_approval_summary
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM client not available - using basic approval summaries")


def human_approval_node(state: Any) -> Dict[str, Any]:
    """
    Human-in-the-loop checkpoint for high-severity anomalies.
    Uses LLM to generate human-readable summaries when available.
    If state.get("streamlit_mode") is True, sets status to pending instead of blocking for input.
    """
    # Convert Pydantic model to dict if needed
    if hasattr(state, 'model_dump'):
        state = state.model_dump()
    elif hasattr(state, 'dict'):
        state = state.dict()

    logger.info("Human approval checkpoint triggered")

    if not state.get("requires_approval"):
        state["approval_status"] = "auto_approved"
        state["logs"] = state.get("logs", []) + ["Auto-approved: no high-severity anomalies"]
        return state

    # Check if running in Streamlit mode
    streamlit_mode = state.get("streamlit_mode", True)

    # If running in Streamlit mode, set as pending for UI approval
    if streamlit_mode:
        state["approval_status"] = "pending"
        state["logs"] = state.get("logs", []) + ["Awaiting Streamlit UI approval"]
        return state

    # Get client name for summary
    client_data = state.get("client_data", {})
    client_name = client_data.get("name", state.get("client_id", "Unknown"))

    # Get analysis and anomalies
    analysis = state.get("analysis_result", {})
    anomalies = analysis.get("anomalies", [])
    high_severity = [a for a in anomalies if a.get("severity") == "high"]

    print("\n" + "=" * 60)
    print("HUMAN-IN-THE-LOOP APPROVAL REQUIRED")
    print("=" * 60)

    # Generate LLM summary if available
    if LLM_AVAILABLE:
        try:
            llm_summary = generate_approval_summary(client_name, analysis, high_severity)
            print(f"\n[AI Summary]\n{llm_summary}\n")
            state["llm_approval_summary"] = llm_summary
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}")
            state["llm_approval_summary"] = None

    print(f"\nClient: {client_name}")
    print(f"High-severity anomalies detected: {len(high_severity)}")

    # Display high-severity anomalies
    print("\n--- Anomalies Requiring Attention ---")
    for i, anomaly in enumerate(high_severity, 1):
        print(f"  {i}. [{anomaly.get('severity').upper()}] {anomaly.get('anomaly_type')}")
        print(f"     {anomaly.get('description')}")

    # Display key metrics
    print(f"\n--- Financial Overview ---")
    print(f"  Net Worth: ${analysis.get('net_worth', 0):,.2f}")
    print(f"  Risk Profile: {analysis.get('risk_profile', 'Unknown').title()}")
    print(f"  Confidence Score: {analysis.get('confidence_score', 0) * 100:.0f}%")

    # Display recommendations count
    recs = analysis.get("recommendations", [])
    print(f"\n  Total Recommendations: {len(recs)}")

    print("\n" + "=" * 60)
    print("Options:")
    print("  [A] Approve - Proceed with recommendations")
    print("  [R] Reject - Flag for manual review")
    print("  [V] View - See full analysis details")
    print("  [D] Details - View recommendations")
    print("=" * 60)

    while True:
        choice = input("\nEnter choice (A/R/V/D): ").strip().upper()

        if choice == "A":
            state["approval_status"] = "approved"
            state["logs"] = state.get("logs", []) + ["Manually approved by user"]
            print("\n[OK] Analysis approved. Proceeding...")
            break
        elif choice == "R":
            state["approval_status"] = "rejected"
            state["logs"] = state.get("logs", []) + ["Manually rejected by user"]
            print("\n[X] Analysis rejected. Flagged for manual review.")
            break
        elif choice == "V":
            print("\n--- Full Analysis ---")
            print(f"Net Worth: ${analysis.get('net_worth', 0):,.2f}")
            print(f"Risk Profile: {analysis.get('risk_profile')}")
            print(f"Confidence Score: {analysis.get('confidence_score', 0) * 100:.0f}%")
            print(f"Anomalies: {len(anomalies)} total ({len(high_severity)} high severity)")
            print(f"\nRecommendations:")
            for rec in recs:
                print(f"  - {rec}")
        elif choice == "D":
            print("\n--- Recommendations ---")
            for i, rec in enumerate(recs, 1):
                # Mark LLM-enhanced recommendations
                llm_marker = " [AI]" if rec in analysis.get("llm_recommendations", []) else ""
                print(f"  {i}. {rec}{llm_marker}")
        else:
            print("Invalid choice. Please enter A, R, V, or D.")

    print("=" * 60 + "\n")
    return state


def should_approve(state: Any) -> str:
    """Conditional routing for human-in-the-loop."""
    # Convert Pydantic model to dict if needed
    if hasattr(state, 'model_dump'):
        state = state.model_dump()
    elif hasattr(state, 'dict'):
        state = state.dict()

    if state.get("requires_approval"):
        return "human_approval"
    return "skip_approval"


def build_workflow():
    """
    Build the LangGraph workflow with nodes and edges.
    """
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("fetcher", fetcher_node)
    workflow.add_node("analyzer", analyzer_node)
    workflow.add_node("human_approval", human_approval_node)

    # Define edges
    workflow.set_entry_point("fetcher")
    workflow.add_edge("fetcher", "analyzer")

    # Conditional edge for human approval
    workflow.add_conditional_edges(
        "analyzer",
        should_approve,
        {
            "human_approval": "human_approval",
            "skip_approval": END
        }
    )

    workflow.add_edge("human_approval", END)

    return workflow.compile()


# Build the workflow
workflow_graph = build_workflow()