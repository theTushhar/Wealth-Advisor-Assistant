"""Pydantic state schema for LangGraph workflow."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class Transaction(BaseModel):
    """Individual transaction record."""
    transaction_id: str
    date: str
    amount: float
    category: str
    description: str
    location: Optional[str] = None


class Anomaly(BaseModel):
    """Detected anomaly in transactions."""
    anomaly_type: str
    description: str
    severity: str
    transaction_id: Optional[str] = None


class ClientData(BaseModel):
    """Client financial data."""
    client_id: str
    name: str
    accounts: List[Dict[str, Any]]
    transactions: List[Transaction]
    risk_tolerance: str
    investment_goals: List[str]


class CRMData(BaseModel):
    """CRM context data."""
    client_id: str
    age: int
    dependents: int
    annual_income: float
    life_events: List[str]


class AnalysisResult(BaseModel):
    """Analysis output from the analyzer agent."""
    net_worth: float
    risk_profile: str
    anomalies: List[Anomaly]
    recommendations: List[str]
    confidence_score: float


class AgentState(BaseModel):
    """
    Main state schema for the LangGraph workflow.
    Passed between nodes and holds all workflow data.
    """
    client_id: str = Field(description="The client identifier")
    client_data: Optional[ClientData] = Field(default=None, description="Client financial data")
    crm_data: Optional[CRMData] = Field(default=None, description="CRM context data")
    analysis_result: Optional[AnalysisResult] = Field(default=None, description="Analysis output")
    errors: List[str] = Field(default_factory=list, description="Error messages")
    logs: List[str] = Field(default_factory=list, description="Execution logs")
    requires_approval: bool = Field(default=False, description="Human-in-the-loop flag")
    approval_status: Optional[str] = Field(default=None, description="Approved/Rejected/Pending")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        arbitrary_types_allowed = True