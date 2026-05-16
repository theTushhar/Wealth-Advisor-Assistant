"""Data Fetcher Agent Node - Retrieves and prepares data from inputs/APIs with LLM validation."""

from typing import Dict, Any
import json
import logging
import os

from tools.crm_tool import fetch_crm_data
from utils.state_utils import to_dict
from utils.llm_client import validate_with_llm, is_llm_available

logger = logging.getLogger(__name__)


def load_client_financial_data(client_id: str) -> Dict[str, Any]:
    """Load client financial data from JSON file."""
    # Path to data file - use absolute path
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "data",
        "mock_client_data.json"
    )

    try:
        with open(data_path, "r") as f:
            data = json.load(f)
            return data.get(client_id, {})
    except FileNotFoundError:
        logger.error(f"Client data file not found: {data_path}")
        return {}
    except json.JSONDecodeError:
        logger.error("Invalid JSON in client data file")
        return {}


def validate_data_completeness(financial_data: Dict[str, Any], crm_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate data completeness using rule-based checks and optionally LLM.

    Returns:
        Dictionary with validation result and any issues found
    """
    issues = []

    # Rule-based validation
    if not financial_data:
        issues.append("No financial data found")
        return {"valid": False, "issues": issues}

    if not financial_data.get("accounts"):
        issues.append("No accounts data available")

    if not financial_data.get("transactions"):
        issues.append("No transactions data available")

    if not financial_data.get("risk_tolerance"):
        issues.append("Risk tolerance not specified")

    if not crm_data:
        issues.append("No CRM data available")

    # LLM validation if available
    if is_llm_available() and financial_data and crm_data:
        try:
            validation_context = f"""
            Analyze this client data for completeness and potential issues:

            Financial Data:
            - Client: {financial_data.get('name')}
            - Accounts: {len(financial_data.get('accounts', []))} accounts
            - Transactions: {len(financial_data.get('transactions', []))} transactions
            - Risk Tolerance: {financial_data.get('risk_tolerance')}
            - Investment Goals: {financial_data.get('investment_goals', [])}

            CRM Data:
            - Age: {crm_data.get('age')}
            - Annual Income: ${crm_data.get('annual_income', 0)}
            - Dependents: {crm_data.get('dependents')}

            Is this data complete and reasonable for a wealth management analysis?
            Identify any potential data quality issues.
            """
            llm_result = validate_with_llm(
                {"financial": financial_data, "crm": crm_data},
                validation_context
            )
            if llm_result.get("llm_response"):
                logger.info(f"LLM validation feedback: {llm_result['llm_response'][:200]}")
        except Exception as e:
            logger.warning(f"LLM validation failed: {e}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "data_quality": "good" if len(issues) == 0 else "needs_review"
    }


def fetcher_node(state: Any) -> Dict[str, Any]:
    """
    Data Fetcher Agent Node - Retrieves and prepares data from inputs/APIs.
    Uses LLM for data validation decisions when available.
    """
    state = to_dict(state)

    client_id = state.get("client_id")
    logger.info(f"Fetcher node processing client: {client_id}")

    updated_state = {
        "logs": state.get("logs", []) + [f"Starting data fetch for {client_id}"]
    }

    try:
        # Load financial data from JSON
        financial_data = load_client_financial_data(client_id)

        if not financial_data:
            updated_state["errors"] = state.get("errors", []) + [f"No financial data found for {client_id}"]
            return updated_state

        # Fetch CRM data using the tool
        crm_result = fetch_crm_data.invoke({"client_id": client_id})

        # Validate data completeness
        validation_result = validate_data_completeness(financial_data, crm_result)

        # Add validation info to state
        updated_state["data_validation"] = {
            "valid": validation_result.get("valid", True),
            "issues": validation_result.get("issues", []),
            "quality": validation_result.get("data_quality", "unknown")
        }

        # Log validation results
        if validation_result.get("issues"):
            for issue in validation_result.get("issues", []):
                updated_state["logs"].append(f"Data issue: {issue}")
                logger.warning(f"Data validation issue for {client_id}: {issue}")

        updated_state["client_data"] = financial_data
        updated_state["crm_data"] = crm_result
        updated_state["logs"] = updated_state["logs"] + [
            f"Financial data loaded: {len(financial_data.get('accounts', []))} accounts",
            f"CRM data fetched: age={crm_result.get('age')}, income=${crm_result.get('annual_income', 0):,.2f}",
            f"Data validation: {validation_result.get('data_quality', 'unknown')}"
        ]

        # LLM decision point: Flag if data needs attention
        if is_llm_available() and validation_result.get("issues"):
            try:
                from utils.llm_client import generate_summary
                decision_prompt = f"""
                The client data for {client_id} has the following issues:
                {', '.join(validation_result.get('issues', []))}

                Should this be flagged for manual review before proceeding with analysis?
                Respond with YES or NO and brief reasoning.
                """
                llm_decision = generate_summary(decision_prompt, "You are a data quality decision assistant.")
                if "YES" in llm_decision.upper()[:50]:
                    updated_state["logs"].append(f"LLM recommends manual review: {llm_decision[:100]}")
            except Exception as e:
                logger.debug(f"LLM decision not available: {e}")

        logger.info(f"Data fetch completed for {client_id}")

    except Exception as e:
        logger.error(f"Error in fetcher node: {str(e)}")
        updated_state["errors"] = state.get("errors", []) + [f"Fetcher error: {str(e)}"]

    return updated_state