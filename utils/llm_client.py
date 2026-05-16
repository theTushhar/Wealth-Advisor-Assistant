"""LLM client setup using ChatOpenAI from langchain-openai."""

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Global LLM instance - lazily initialized
_llm_instance: Optional[ChatOpenAI] = None


def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """
    Get or create the ChatOpenAI LLM instance.

    Args:
        temperature: Sampling temperature for the LLM (0.0 to 1.0)

    Returns:
        ChatOpenAI instance configured from environment variables
    """
    global _llm_instance

    if _llm_instance is not None:
        return _llm_instance

    # Load configuration from environment
    api_key = os.getenv("OPENAI_API_KEY")
    model_name = os.getenv("LLM_MODEL")

    if not api_key:
        logger.warning("OPENAI_API_KEY not found in environment")
        raise ValueError("OPENAI_API_KEY is required but not set in environment")

    if not model_name:
        logger.warning("LLM_MODEL not found in environment")
        raise ValueError("LLM_MODEL is required but not set in environment")

    _llm_instance = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=api_key,
        max_tokens=1000,
        timeout=30.0
    )

    logger.info(f"LLM initialized with model: {model_name}")
    return _llm_instance


def generate_summary(prompt: str, system_message: Optional[str] = None) -> str:
    """
    Generate a text summary using the LLM.

    Args:
        prompt: The user prompt/question
        system_message: Optional system message for context

    Returns:
        Generated text response from the LLM
    """
    llm = get_llm(temperature=0.5)

    messages = []
    if system_message:
        messages.append(SystemMessage(content=system_message))
    messages.append(HumanMessage(content=prompt))

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"LLM generation failed: {str(e)}")
        return f"Error generating summary: {str(e)}"


def validate_with_llm(data: Dict[str, Any], validation_prompt: str) -> Dict[str, Any]:
    """
    Use LLM to validate or make decisions about data.

    Args:
        data: The data to validate
        validation_prompt: Prompt template for validation

    Returns:
        Dictionary with validation result and reasoning
    """
    llm = get_llm(temperature=0.3)

    # Build context from data
    context = f"Data: {data}\n\nValidation question: {validation_prompt}"

    messages = [
        SystemMessage(content="You are a financial data validation assistant. Analyze the data and provide a validation result with clear reasoning."),
        HumanMessage(content=context)
    ]

    try:
        response = llm.invoke(messages)
        return {
            "valid": True,
            "llm_response": response.content,
            "confidence": 0.8
        }
    except Exception as e:
        logger.error(f"LLM validation failed: {str(e)}")
        return {
            "valid": False,
            "error": str(e),
            "confidence": 0.0
        }


def generate_recommendations_with_llm(
    net_worth: float,
    risk_profile: str,
    anomalies: List[Dict[str, Any]],
    crm_data: Dict[str, Any]
) -> List[str]:
    """
    Use LLM to generate enriched recommendations.

    Args:
        net_worth: Client's calculated net worth
        risk_profile: Determined risk profile
        anomalies: List of detected anomalies
        crm_data: CRM context data

    Returns:
        List of LLM-generated recommendations
    """
    llm = get_llm(temperature=0.7)

    # Build context
    context = f"""
Client Profile:
- Net Worth: ${net_worth:,.2f}
- Risk Profile: {risk_profile}
- Age: {crm_data.get('age', 'Unknown')}
- Annual Income: ${crm_data.get('annual_income', 0):,.2f}
- Dependents: {crm_data.get('dependents', 0)}
- Life Events: {crm_data.get('life_events', [])}

Anomalies Detected:
{chr(10).join([f"- {a.get('anomaly_type')}: {a.get('description')} (Severity: {a.get('severity')})" for a in anomalies])}

Based on this analysis, provide 3-5 specific, actionable recommendations for a financial advisor to discuss with the client. Focus on:
1. Risk management based on the client's life stage
2. Action items to address anomalies
3. Wealth optimization opportunities
4. Goal-based financial planning recommendations
"""

    messages = [
        SystemMessage(content="You are a Wealth Advisor Assistant. Generate specific, actionable financial recommendations."),
        HumanMessage(content=context)
    ]

    try:
        response = llm.invoke(messages)
        # Parse recommendations from response (split by newlines or numbered items)
        recommendations = []
        for line in response.content.split('\n'):
            line = line.strip()
            # Remove common prefixes like "1.", "-", "*"
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                clean_line = line.lstrip('0123456789.-* ').strip()
                if clean_line:
                    recommendations.append(clean_line)

        # Fallback to whole response if parsing fails
        if not recommendations:
            recommendations = [response.content]

        return recommendations[:5]  # Limit to 5 recommendations
    except Exception as e:
        logger.error(f"LLM recommendation generation failed: {str(e)}")
        return ["Error generating recommendations - please review manually"]


def generate_approval_summary(
    client_name: str,
    analysis_result: Dict[str, Any],
    anomalies: List[Dict[str, Any]]
) -> str:
    """
    Generate a human-readable summary for human-in-the-loop approval.

    Args:
        client_name: Client's name
        analysis_result: Full analysis results
        anomalies: List of high-severity anomalies

    Returns:
        Formatted summary string for approval prompt
    """
    llm = get_llm(temperature=0.5)

    context = f"""
Generate a brief, professional summary for a financial advisor to review before client consultation.

Client: {client_name}

Financial Overview:
- Net Worth: ${analysis_result.get('net_worth', 0):,.2f}
- Risk Profile: {analysis_result.get('risk_profile', 'Unknown')}

High-Priority Anomalies Requiring Attention:
{chr(10).join([f"- {a.get('anomaly_type')}: {a.get('description')}" for a in anomalies])}

Existing Recommendations:
{chr(10).join([f"- {r}" for r in analysis_result.get('recommendations', [])])}

Provide a concise summary (3-4 sentences) highlighting the key findings and what requires immediate attention.
"""

    messages = [
        SystemMessage(content="You are a financial advisory assistant. Generate concise, professional summaries."),
        HumanMessage(content=context)
    ]

    try:
        response = llm.invoke(messages)
        return response.content
    except Exception as e:
        logger.error(f"LLM approval summary generation failed: {str(e)}")
        # Fallback to basic summary
        return f"Analysis for {client_name}: Net Worth ${analysis_result.get('net_worth', 0):,.2f}. {len(anomalies)} high-severity anomalies detected requiring review."


def clear_llm_instance():
    """Clear the global LLM instance (useful for testing)."""
    global _llm_instance
    _llm_instance = None
    logger.info("LLM instance cleared")