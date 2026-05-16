"""CRM tool using LangChain @tool decorator."""

from langchain_core.tools import tool
from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


@tool
def fetch_crm_data(client_id: str) -> Dict[str, Any]:
    """
    Fetch CRM data for a client including demographics and life events.

    Args:
        client_id: The unique identifier for the client

    Returns:
        Dictionary containing CRM data (age, dependents, income, life events)
    """
    logger.info(f"Fetching CRM data for client: {client_id}")

    # Simulate API latency
    time.sleep(0.5)

    # Mock CRM database - in production, this would call an actual CRM API
    crm_database = {
        "C-12345": {
            "client_id": "C-12345",
            "age": 45,
            "dependents": 2,
            "annual_income": 150000.0,
            "life_events": ["Recently married", "New home purchase"]
        },
        "C-67890": {
            "client_id": "C-67890",
            "age": 32,
            "dependents": 0,
            "annual_income": 95000.0,
            "life_events": ["Career transition"]
        }
    }

    if client_id in crm_database:
        logger.info(f"CRM data retrieved for {client_id}")
        return crm_database[client_id]
    else:
        logger.warning(f"No CRM data found for client: {client_id}")
        # Return default data for unknown clients
        return {
            "client_id": client_id,
            "age": 35,
            "dependents": 0,
            "annual_income": 75000.0,
            "life_events": []
        }