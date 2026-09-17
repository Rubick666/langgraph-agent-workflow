from typing import Optional, TypedDict


class TicketState(TypedDict, total=False):
    """Shared state passed between graph nodes.

    `total=False` means every key is optional — nodes only set what they
    know, and later nodes can read what earlier nodes wrote.
    """
    # Input
    ticket_text: str

    # Classification
    category: Optional[str]          # billing / technical / shipping / account / other
    is_confident: Optional[bool]     # False → route to human_review

    # Policy + decision
    policy_reference: Optional[str]
    decision: Optional[str]          # "respond" | "escalate" | "human_review"

    # Output
    draft_response: Optional[str]

    # Observability: each node appends a trace entry
    trace: list[dict]