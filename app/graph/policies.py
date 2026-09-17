POLICIES: dict[str, str] = {
    "billing": (
        "Billing policy: Refunds are issued within 5 business days for duplicate charges. "
        "If the charge is confirmed to be legitimate, explain the line item and offer to review the account."
    ),
    "technical": (
        "Technical policy: Ask the customer for the model, version, and steps to reproduce. "
        "If the issue cannot be resolved in two exchanges, escalate to the engineering team."
    ),
    "shipping": (
        "Shipping policy: Standard delivery is 3–5 business days. If the package is more than 5 days late, "
        "offer a replacement or full refund, and file a carrier claim."
    ),
    "account": (
        "Account policy: Password resets require verifying the account email. Changes to billing details "
        "require a confirmation email to the registered address."
    ),
    "other": (
        "General policy: For issues that don't fit a category, ask one clarifying question before escalating."
    ),
}


def get_policy(category: str) -> str:
    return POLICIES.get(category, POLICIES["other"])