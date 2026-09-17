from typing import Optional

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    ticket_text: str = Field(..., min_length=5, max_length=4000)


class RunResponse(BaseModel):
    category: str
    is_confident: bool
    trace: list[dict]

    policy_reference: Optional[str] = None
    decision: Optional[str] = None
    draft_response: Optional[str] = None