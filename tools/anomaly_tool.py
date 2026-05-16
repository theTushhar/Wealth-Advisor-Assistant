"""Anomaly detection tool using LangChain @tool decorator."""

from langchain_core.tools import tool
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


@tool
def detect_anomalies(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Detect anomalies in financial transactions using rule-based detection.

    Args:
        transactions: List of transaction dictionaries

    Returns:
        List of detected anomalies with type, description, and severity
    """
    logger.info(f"Analyzing {len(transactions)} transactions for anomalies")

    anomalies = []

    # Rule 1: Large transactions (>$10,000)
    for txn in transactions:
        amount = txn.get("amount", 0)
        if amount > 10000:
            anomalies.append({
                "anomaly_type": "large_transaction",
                "description": f"Unusually large transaction of ${amount:,.2f}",
                "severity": "high",
                "transaction_id": txn.get("transaction_id")
            })
            logger.warning(f"Large transaction detected: ${amount:,.2f}")

    # Rule 2: Multiple transactions in short timeframe
    # Simplified: check for same-day transactions
    transaction_dates = {}
    for txn in transactions:
        date = txn.get("date")
        if date:
            if date not in transaction_dates:
                transaction_dates[date] = []
            transaction_dates[date].append(txn)

    for date, txns in transaction_dates.items():
        if len(txns) > 5:
            anomalies.append({
                "anomaly_type": "high_frequency",
                "description": f"High transaction frequency: {len(txns)} transactions on {date}",
                "severity": "medium",
                "transaction_id": None
            })

    # Rule 3: Unusual locations (if available)
    for txn in transactions:
        location = txn.get("location", "").lower()
        if location and location not in ["new york", "los angeles", "chicago", "local"]:
            anomalies.append({
                "anomaly_type": "unusual_location",
                "description": f"Transaction in unusual location: {txn.get('location')}",
                "severity": "low",
                "transaction_id": txn.get("transaction_id")
            })

    logger.info(f"Detected {len(anomalies)} anomalies")
    return anomalies