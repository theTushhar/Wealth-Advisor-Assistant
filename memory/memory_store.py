"""Memory layer with short-term (session), long-term (persistent) storage, and LLM-generated summaries."""

from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Try to import LLM client - graceful fallback if not available
try:
    from utils.llm_client import generate_summary as llm_generate_summary
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLM client not available - using basic summaries")


class MemoryStore:
    """
    Memory layer with short-term (session), long-term (persistent) storage,
    and LLM-generated summaries for enhanced context.
    """

    def __init__(self, storage_path: str = "memory_store.json"):
        self.storage_path = storage_path
        self.short_term: Dict[str, Any] = {}  # Session context
        self.long_term: List[Dict[str, Any]] = self._load_long_term()

    def _load_long_term(self) -> List[Dict[str, Any]]:
        """Load long-term memory from persistent storage."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def _save_long_term(self):
        """Save long-term memory to persistent storage."""
        try:
            with open(self.storage_path, "w") as f:
                json.dump(self.long_term[-100:], f, indent=2)  # Keep last 100 entries
        except IOError as e:
            logger.error(f"Failed to save long-term memory: {e}")

    def add_session_context(self, key: str, value: Any):
        """Add to short-term memory (session context)."""
        self.short_term[key] = value
        logger.debug(f"Added to short-term memory: {key}")

    def get_session_context(self, key: str, default: Any = None) -> Any:
        """Retrieve from short-term memory."""
        return self.short_term.get(key, default)

    def store_analysis(self, client_id: str, analysis_result: Dict[str, Any]):
        """Store analysis result in long-term memory."""
        # Generate LLM summary if available
        summary = self._generate_llm_summary(client_id, analysis_result)

        entry = {
            "client_id": client_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis_result,
            "llm_summary": summary
        }
        self.long_term.append(entry)
        self._save_long_term()
        logger.info(f"Stored analysis for {client_id} in long-term memory")

    def _generate_llm_summary(self, client_id: str, analysis_result: Dict[str, Any]) -> Optional[str]:
        """Generate LLM summary for analysis result."""
        if not LLM_AVAILABLE:
            # Fallback to basic summary
            return self._basic_summary(client_id, analysis_result)

        try:
            prompt = f"""
            Generate a brief summary (2-3 sentences) of this financial analysis for a client.

            Client ID: {client_id}
            Net Worth: ${analysis_result.get('net_worth', 0):,.2f}
            Risk Profile: {analysis_result.get('risk_profile', 'Unknown')}
            Anomalies: {len(analysis_result.get('anomalies', []))} detected
            Recommendations: {len(analysis_result.get('recommendations', []))} generated

            Focus on key financial health indicators and any concerns.
            """
            summary = llm_generate_summary(prompt)
            logger.info(f"Generated LLM summary for {client_id}")
            return summary
        except Exception as e:
            logger.warning(f"LLM summary generation failed: {e}")
            return self._basic_summary(client_id, analysis_result)

    def _basic_summary(self, client_id: str, analysis_result: Dict[str, Any]) -> str:
        """Generate basic summary without LLM."""
        net_worth = analysis_result.get("net_worth", 0)
        risk_profile = analysis_result.get("risk_profile", "Unknown")
        anomaly_count = len(analysis_result.get("anomalies", []))

        return f"Client {client_id}: Net worth ${net_worth:,.2f}, Risk profile: {risk_profile}, {anomaly_count} anomalies detected."

    def get_client_history(self, client_id: str) -> List[Dict[str, Any]]:
        """Retrieve historical analyses for a client."""
        return [
            entry for entry in self.long_term
            if entry.get("client_id") == client_id
        ]

    def get_latest_summary(self, client_id: str) -> Optional[str]:
        """Get the most recent LLM summary for a client."""
        history = self.get_client_history(client_id)
        if history:
            return history[-1].get("llm_summary")
        return None

    def get_session_summary(self) -> str:
        """Generate a summary of current session context using LLM."""
        if not self.short_term:
            return "No session context available."

        # Build context from short-term memory
        context_parts = []
        for key, value in self.short_term.items():
            if isinstance(value, dict):
                context_parts.append(f"{key}: {json.dumps(value)[:100]}...")
            else:
                context_parts.append(f"{key}: {str(value)[:100]}")

        context = "\n".join(context_parts)

        if LLM_AVAILABLE:
            try:
                prompt = f"""
                Summarize the current session context for a financial advisor workflow:

                {context}

                Provide a brief overview of what's been processed in this session.
                """
                return llm_generate_summary(prompt)
            except Exception as e:
                logger.warning(f"Session summary LLM failed: {e}")

        # Fallback
        return f"Session has {len(self.short_term)} context entries: {list(self.short_term.keys())}"

    def clear_session(self):
        """Clear short-term memory."""
        self.short_term = {}
        logger.info("Short-term memory cleared")

    def get_all_summaries(self) -> List[Dict[str, Any]]:
        """Get all LLM summaries from long-term memory."""
        return [
            {
                "client_id": entry.get("client_id"),
                "timestamp": entry.get("timestamp"),
                "summary": entry.get("llm_summary", "No summary available")
            }
            for entry in self.long_term[-10:]  # Last 10 entries
        ]


# Global memory instance
memory_store = MemoryStore()