"""Main entry point for the Wealth Advisor Assistant."""

import sys
import json
import logging
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from utils.logger import logger
from graph.workflow import workflow_graph
from memory.memory_store import memory_store


def run_analysis(client_id: str, streamlit_mode: bool = True) -> Dict[str, Any]:
    """
    Run the full wealth advisor analysis workflow.
    Set streamlit_mode=False for CLI mode (blocking input).
    """
    logger.info(f"Starting analysis for client: {client_id}")

    # Initialize state
    initial_state = {
        "client_id": client_id,
        "client_data": None,
        "crm_data": None,
        "analysis_result": None,
        "errors": [],
        "logs": [],
        "requires_approval": False,
        "approval_status": None,
        "streamlit_mode": streamlit_mode
    }

    try:
        # Execute workflow
        result = workflow_graph.invoke(initial_state)

        # Store in memory
        if result.get("analysis_result"):
            memory_store.store_analysis(
                client_id,
                result["analysis_result"]
            )

        logger.info(f"Analysis completed for {client_id}")
        return result

    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        return {
            "client_id": client_id,
            "errors": [str(e)],
            "logs": [f"Critical error: {str(e)}"]
        }


def display_results(result: Dict[str, Any]):
    """Display formatted analysis results."""
    print("\n" + "=" * 60)
    print("WEALTH ADVISOR ANALYSIS REPORT")
    print("=" * 60)

    print(f"\nClient ID: {result.get('client_id')}")

    analysis = result.get("analysis_result")
    if analysis:
        print(f"\n Net Worth: ${analysis.get('net_worth', 0):,.2f}")
        print(f" Risk Profile: {analysis.get('risk_profile').title()}")

        print(f"\n Anomalies Detected: {len(analysis.get('anomalies', []))}")
        for anomaly in analysis.get("anomalies", []):
            severity_icon = "[H]" if anomaly.get("severity") == "high" else "[M]" if anomaly.get("severity") == "medium" else "[L]"
            print(f"  {severity_icon} {anomaly.get('anomaly_type')}: {anomaly.get('description')}")

        print(f"\n Recommendations:")
        for rec in analysis.get("recommendations", []):
            print(f"  - {rec}")

        print(f"\n Confidence Score: {analysis.get('confidence_score', 0) * 100:.0f}%")
    else:
        print("\n[!] No analysis results available")

    errors = result.get("errors", [])
    if errors:
        print(f"\n Errors: {errors}")

    print("\n Execution Logs:")
    for log in result.get("logs", []):
        print(f"  - {log}")

    print("\n" + "=" * 60 + "\n")


def main():
    """Main entry point for the Wealth Advisor Assistant."""
    print("Wealth Advisor Assistant - Multi-Agent System")
    print("Using LangChain/LangGraph\n")

    # Interactive mode
    while True:
        client_id = input("Enter client ID (or 'quit' to exit): ").strip()

        if client_id.lower() in ["quit", "exit", "q"]:
            print("Exiting...")
            break

        if not client_id:
            print("Please enter a valid client ID")
            continue

        result = run_analysis(client_id)
        display_results(result)


if __name__ == "__main__":
    main()