"""Analyzer Agent Node - Performs financial analysis with LLM-enhanced reasoning."""

from typing import Dict, Any, List
import logging

from constants import RISK_PROFILES, SEVERITY_LEVELS
from tools.anomaly_tool import detect_anomalies

logger = logging.getLogger(__name__)

# Try to import LLM client - graceful fallback
try:
    from utils.llm_client import generate_recommendations_with_llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM client not available - using rule-based recommendations only")


def calculate_net_worth(accounts: List[Dict[str, Any]]) -> float:
    """Calculate total net worth from accounts."""
    total = 0.0
    for account in accounts:
        balance = account.get("balance", 0)
        account_type = account.get("type", "").lower()

        # Treat liabilities as negative
        if account_type in ["credit", "loan", "mortgage"]:
            total -= abs(balance)
        else:
            total += balance

    return total


def determine_risk_profile(risk_tolerance: str, age: int, dependents: int) -> str:
    """Determine risk profile based on multiple factors."""
    risk_lower = risk_tolerance.lower()

    # Adjust based on life stage
    if age > 55:
        return "conservative"
    elif age < 30 and dependents == 0:
        return "aggressive" if risk_lower == "high" else "moderate"
    else:
        return risk_lower if risk_lower in RISK_PROFILES else "moderate"


def generate_rule_based_recommendations(net_worth: float, anomalies: List[Dict], risk_profile: str) -> List[str]:
    """Generate preliminary recommendations based on analysis rules."""
    recommendations = []

    # Net worth based
    if net_worth < 50000:
        recommendations.append("Consider building emergency fund before investing")
    elif net_worth > 500000:
        recommendations.append("Explore diversified investment opportunities")

    # Anomaly based
    high_severity = [a for a in anomalies if a.get("severity") == "high"]
    if high_severity:
        recommendations.append("Review high-severity anomalies with client")

    # Risk profile based
    if risk_profile == "conservative":
        recommendations.append("Consider bonds and stable income vehicles")
    elif risk_profile == "aggressive":
        recommendations.append("Explore growth-oriented portfolio allocation")

    return recommendations


def analyze_anomaly_patterns(anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze patterns in detected anomalies using rule-based logic."""
    severity_counts = {level: 0 for level in SEVERITY_LEVELS}
    anomaly_types = {}

    for anomaly in anomalies:
        severity = anomaly.get("severity", "low")
        anomaly_type = anomaly.get("anomaly_type", "unknown")

        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        anomaly_types[anomaly_type] = anomaly_types.get(anomaly_type, 0) + 1

    return {
        "severity_distribution": severity_counts,
        "types": anomaly_types,
        "requires_attention": severity_counts.get("high", 0) > 0
    }


def analyzer_node(state: Any) -> Dict[str, Any]:
    """
    Analyzer Agent Node - Performs financial analysis with LLM enhancement.
    Combines rule-based analysis with LLM for enriched recommendations.
    """
    # Convert Pydantic model to dict if needed
    if hasattr(state, 'model_dump'):
        state = state.model_dump()
    elif hasattr(state, 'dict'):
        state = state.dict()

    logger.info("Analyzer node processing")

    updated_state = {
        "logs": state.get("logs", []) + ["Starting analysis"]
    }

    try:
        client_data = state.get("client_data")

        if not client_data:
            updated_state["errors"] = state.get("errors", []) + ["No client data to analyze"]
            return updated_state

        # Extract transactions for anomaly detection
        transactions = client_data.get("transactions", [])
        txn_dicts = [dict(t) if hasattr(t, '__dict__') else t for t in transactions]

        # Detect anomalies
        anomaly_result = detect_anomalies.invoke({"transactions": txn_dicts})

        # Analyze anomaly patterns
        anomaly_analysis = analyze_anomaly_patterns(anomaly_result)

        # Calculate net worth
        accounts = client_data.get("accounts", [])
        net_worth = calculate_net_worth(accounts)

        # Get CRM context
        crm_data = state.get("crm_data", {})
        age = crm_data.get("age", 35)
        dependents = crm_data.get("dependents", 0)

        # Determine risk profile
        risk_tolerance = client_data.get("risk_tolerance", "moderate")
        risk_profile = determine_risk_profile(risk_tolerance, age, dependents)

        # Generate rule-based recommendations
        rule_recommendations = generate_rule_based_recommendations(net_worth, anomaly_result, risk_profile)

        # LLM-enhanced recommendations
        llm_recommendations = []
        if LLM_AVAILABLE:
            try:
                llm_recommendations = generate_recommendations_with_llm(
                    net_worth=net_worth,
                    risk_profile=risk_profile,
                    anomalies=anomaly_result,
                    crm_data=crm_data
                )
                logger.info(f"Generated {len(llm_recommendations)} LLM recommendations")
                updated_state["logs"].append(f"LLM recommendations generated: {len(llm_recommendations)}")
            except Exception as e:
                logger.warning(f"LLM recommendation generation failed: {e}")
                llm_recommendations = []

        # Combine recommendations - merge unique ones
        all_recommendations = rule_recommendations.copy()
        for rec in llm_recommendations:
            # Simple deduplication check
            if rec not in all_recommendations:
                all_recommendations.append(rec)

        # Build analysis result with enhanced metadata
        analysis_result = {
            "net_worth": net_worth,
            "risk_profile": risk_profile,
            "anomalies": anomaly_result,
            "anomaly_analysis": anomaly_analysis,
            "recommendations": all_recommendations,
            "rule_recommendations": rule_recommendations,
            "llm_recommendations": llm_recommendations,
            "confidence_score": 0.85 if not LLM_AVAILABLE else 0.92,
            "llm_enhanced": LLM_AVAILABLE
        }

        updated_state["analysis_result"] = analysis_result

        # Determine if human approval is needed
        high_severity_count = len([a for a in anomaly_result if a.get("severity") == "high"])
        updated_state["requires_approval"] = high_severity_count > 0

        # Get severity counts from anomaly analysis for logging
        severity_counts = anomaly_analysis.get("severity_distribution", {})

        updated_state["logs"] = updated_state["logs"] + [
            f"Net worth calculated: ${net_worth:,.2f}",
            f"Risk profile: {risk_profile}",
            f"Anomalies found: {len(anomaly_result)} (High: {severity_counts.get('high', 0)}, Medium: {severity_counts.get('medium', 0)}, Low: {severity_counts.get('low', 0)})",
            f"Recommendations: {len(all_recommendations)} total ({len(rule_recommendations)} rule-based, {len(llm_recommendations)} LLM-enhanced)"
        ]

        # Log LLM status
        if LLM_AVAILABLE:
            logger.info("Analysis enhanced with LLM recommendations")
        else:
            logger.info("Analysis using rule-based recommendations only")

    except Exception as e:
        logger.error(f"Error in analyzer node: {str(e)}")
        updated_state["errors"] = state.get("errors", []) + [f"Analyzer error: {str(e)}"]

    return updated_state