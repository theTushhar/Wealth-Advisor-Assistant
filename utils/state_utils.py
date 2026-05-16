"""State utility functions for converting between different state representations."""

from typing import Any, Dict


def to_dict(state: Any) -> Dict[str, Any]:
    """
    Convert state to dict, handling Pydantic models.

    Args:
        state: The state object (can be Pydantic model, dict, or other)

    Returns:
        Dictionary representation of the state
    """
    if hasattr(state, 'model_dump'):
        return state.model_dump()
    elif hasattr(state, 'dict'):
        return state.dict()
    return state