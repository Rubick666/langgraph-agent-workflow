from typing import Any, Optional
from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    ticket_text: str = Field(..., min_length=5, max_length=4000)


class ResumeRequest(BaseModel):
    """Human decision when resuming an interrupted run.

    For a classification review:
      {"action": "confirm"}
      {"action": "override", "category": "billing"}

    For an escalation review:
      {"action": "approve"}   # escalate to a human
      {"action": "respond"}   # attempt an automated reply
    """
    action: str = Field(..., description="confirm | override | approve | respond")
    category: Optional[str] = Field(None, description="Only for override during classification review")
    note: Optional[str] = Field(None, description="Optional free-form note")


class WorkflowState(BaseModel):
    ticket_text: Optional[str] = None
    category: Optional[str] = None
    is_confident: Optional[bool] = None
    policy_reference: Optional[str] = None
    decision: Optional[str] = None
    draft_response: Optional[str] = None
    human_action: Optional[str] = None
    human_note: Optional[str] = None
    trace: list[dict] = Field(default_factory=list)


class RunResponse(BaseModel):
    run_id: str
    status: str  # "completed" | "awaiting_review"
    state: WorkflowState
    interrupt: Optional[dict] = None