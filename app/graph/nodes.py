from app.core.llm import llm
from app.graph.state import TicketState
from app.graph.policies import get_policy

ALLOWED_CATEGORIES = {"billing", "technical", "shipping", "account", "other"}


async def classify_node(state: TicketState) -> dict:
    ticket = state["ticket_text"]

    prompt = (
        "Classify the customer-support ticket into exactly ONE of these categories:\n"
        "billing, technical, shipping, account, other\n\n"
        "Examples:\n"
        "- 'I was charged twice.' → billing\n"
        "- 'The app crashes on login.' → technical\n"
        "- 'My package is late.' → shipping\n"
        "- 'I need to reset my password.' → account\n"
        "- 'Just wanted to say thanks.' → other\n\n"
        "Respond with only the category name in lowercase, no punctuation.\n\n"
        f"Ticket:\n{ticket}\n\n"
        "Category:"
    )

    response = await llm.ainvoke(prompt)
    raw = (response.content or "").strip().lower()
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

async def retrieve_policy_node(state: TicketState) -> dict:
    """Look up the policy text for the classified category."""
    category = state.get("category", "other")
    policy = get_policy(category)

    return {
        "policy_reference": policy,
        "trace": state.get("trace", []) + [
            {"node": "retrieve_policy", "category": category}
        ],
    }


async def decide_node(state: TicketState) -> dict:
    """Decide whether to respond directly or escalate to a human.

    Rule of thumb: escalate ONLY when the policy does not cover the case,
    or the customer is explicitly demanding a human.
    """
    ticket = state["ticket_text"]
    policy = state.get("policy_reference", "")
    category = state.get("category", "other")

    prompt = (
        "You decide whether a support agent can answer using the policy, "
        "or whether the ticket must be escalated to a human.\n\n"
        "Escalate ONLY if:\n"
        "- The policy does not cover the customer's request, OR\n"
        "- The customer explicitly asks for a human.\n"
        "Otherwise, respond.\n\n"
        "Examples:\n"
        "- 'I was charged twice, please refund.' → respond\n"
        "- 'My package is late.' → respond\n"
        "- 'I want to speak to a manager.' → escalate\n"
        "- 'You broke my custom integration, I need a senior engineer.' → escalate\n\n"
        "Reply with exactly one word: respond or escalate.\n\n"
        f"Category: {category}\n"
        f"Policy: {policy}\n"
        f"Ticket:\n{ticket}\n\n"
        "Decision:"
    )

    response = await llm.ainvoke(prompt)
    raw = (response.content or "").strip().lower()
    decision = raw.split()[0].strip(".,!?:;\"'") if raw else ""
    if decision not in {"respond", "escalate"}:
        decision = "respond"   # safer default: policy almost always covers something

    return {
        "decision": decision,
        "trace": state.get("trace", []) + [
            {"node": "decide", "decision": decision, "raw": raw}
        ],
    }


async def draft_node(state: TicketState) -> dict:
    """Draft a short, professional reply to the customer."""
    ticket = state["ticket_text"]
    policy = state.get("policy_reference", "")
    category = state.get("category", "other")

    prompt = (
        "You are a customer-support agent. Write a short (2–3 sentence) professional "
        "reply to the ticket below. Ground your reply in the policy. "
        "Do not invent facts. Do not include placeholders like [Name].\n\n"
        f"Category: {category}\n"
        f"Policy: {policy}\n"
        f"Ticket:\n{ticket}\n\n"
        "Reply:"
    )

    response = await llm.ainvoke(prompt)
    draft = (response.content or "").strip()

    return {
        "draft_response": draft,
        "trace": state.get("trace", []) + [
            {"node": "draft", "chars": len(draft)}
        ],
    }


async def human_review_node(state: TicketState) -> dict:
    """Terminal node for low-confidence tickets.

    For now this simply marks the run as needing human review.
    In Step 3 we'll add checkpointing so a run can be paused here and resumed.
    """
    return {
        "decision": "human_review",
        "draft_response": None,
        "trace": state.get("trace", []) + [
            {"node": "human_review", "reason": "low classification confidence"}
        ],
    }