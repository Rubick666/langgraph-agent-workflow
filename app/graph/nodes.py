from app.core.llm import llm
from app.graph.state import TicketState

ALLOWED_CATEGORIES = {"billing", "technical", "shipping", "account", "other"}


async def classify_node(state: TicketState) -> dict:
    """Classify a support ticket into one of a fixed set of categories.

    Uses a strict prompt that asks for a single word. If the model's output
    is not in the allowed set, we treat it as low confidence and route to
    human review downstream.
    """
    ticket = state["ticket_text"]

    prompt = (
        "You are a customer-support triage assistant. "
        "Classify the ticket below into exactly ONE of these categories:\n"
        "billing, technical, shipping, account, other\n\n"
        "Respond with only the category name in lowercase, no punctuation.\n\n"
        f"Ticket:\n{ticket}\n\n"
        "Category:"
    )

    response = await llm.ainvoke(prompt)
    raw = (response.content or "").strip().lower()
    # Take the first token, strip punctuation
    category = raw.split()[0].strip(".,!?:;\"'") if raw else ""

    is_confident = category in ALLOWED_CATEGORIES
    if not is_confident:
        category = "other"

    return {
        "category": category,
        "is_confident": is_confident,
        "trace": state.get("trace", []) + [
            {"node": "classify", "category": category, "raw": raw, "is_confident": is_confident}
        ],
    }