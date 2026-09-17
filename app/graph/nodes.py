from langgraph.types import interrupt

from app.core.llm import llm
from app.graph.policies import get_policy
from app.graph.state import TicketState

ALLOWED_CATEGORIES = {"billing", "technical", "shipping", "account", "other"}


# ---------------------------------------------------------------- classify
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


# --------------------------------------------------- review_classification
async def review_classification_node(state: TicketState) -> dict:
    """Pause the graph and ask a human to confirm or override the category."""
    payload = {
        "reason": "low_classification_confidence",
        "ticket_text": state.get("ticket_text"),
        "suggested_category": state.get("category", "other"),
        "allowed_categories": sorted(ALLOWED_CATEGORIES),
        "instructions": (
            "Reply with {'action': 'confirm'} to keep the suggested category, "
            "or {'action': 'override', 'category': '<one of allowed_categories>'}."
        ),
    }

    # -------- the graph pauses here --------
    human = interrupt(payload)
    # -------- on resume, `human` is what the client sent --------

    if human.get("action") == "override" and human.get("category") in ALLOWED_CATEGORIES:
        category = human["category"]
    else:
        category = state.get("category", "other")

    return {
        "category": category,
        "is_confident": True,           # human-confirmed
        "human_action": human.get("action"),
        "human_note": human.get("note"),
        "trace": state.get("trace", []) + [
            {"node": "review_classification", "final_category": category, "human": human}
        ],
    }


# ------------------------------------------------------- retrieve_policy
async def retrieve_policy_node(state: TicketState) -> dict:
    category = state.get("category", "other")
    policy = get_policy(category)
    return {
        "policy_reference": policy,
        "trace": state.get("trace", []) + [{"node": "retrieve_policy", "category": category}],
    }


# ---------------------------------------------------------------- decide
async def decide_node(state: TicketState) -> dict:
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
        decision = "respond"

    return {
        "decision": decision,
        "trace": state.get("trace", []) + [
            {"node": "decide", "decision": decision, "raw": raw}
        ],
    }


# ------------------------------------------------------ review_escalation
async def review_escalation_node(state: TicketState) -> dict:
    """Pause the graph and ask a human to approve escalation or force a response."""
    payload = {
        "reason": "escalation_requires_approval",
        "ticket_text": state.get("ticket_text"),
        "category": state.get("category"),
        "policy_reference": state.get("policy_reference"),
        "suggested_decision": state.get("decision"),
        "instructions": (
            "Reply with {'action': 'approve'} to escalate to a human agent, "
            "or {'action': 'respond'} to attempt an automated reply."
        ),
    }

    human = interrupt(payload)

    action = human.get("action")
    new_decision = "escalate" if action == "approve" else "respond"

    return {
        "decision": new_decision,
        "human_action": action,
        "human_note": human.get("note"),
        "trace": state.get("trace", []) + [
            {"node": "review_escalation", "final_decision": new_decision, "human": human}
        ],
    }


# ---------------------------------------------------------------- draft
async def draft_node(state: TicketState) -> dict:
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
        "trace": state.get("trace", []) + [{"node": "draft", "chars": len(draft)}],
    }