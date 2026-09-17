from typing import Optional, TypedDict


class TicketState(TypedDict, total=False):
    # Input
    ticket_text: str

    # Classification
    category: Optional[str]
    is_confident: Optional[bool]

    # Policy + decision
    policy_reference: Optional[str]
    decision: Optional[str]          # "respond" | "escalate"

    # Human review (populated when a run is resumed)
    human_action: Optional[str]      # "confirm" | "override" | "approve" | "respond"
    human_note: Optional[str]

    # Output
    draft_response: Optional[str]

    # Observability
    trace: list[dict]