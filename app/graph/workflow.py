from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import (
    classify_node,
    decide_node,
    draft_node,
    human_review_node,
    retrieve_policy_node,
)
from app.graph.state import TicketState


def _route_after_classify(state: TicketState) -> str:
    """Conditional edge: confident → normal path, otherwise → human review."""
    return "retrieve_policy" if state.get("is_confident") else "human_review"


def _build_graph():
    g = StateGraph(TicketState)

    # Nodes
    g.add_node("classify", classify_node)
    g.add_node("retrieve_policy", retrieve_policy_node)
    g.add_node("decide", decide_node)
    g.add_node("draft", draft_node)
    g.add_node("human_review", human_review_node)

    # Entry
    g.add_edge(START, "classify")

    # Conditional branch after classification
    g.add_conditional_edges(
        "classify",
        _route_after_classify,
        {
            "retrieve_policy": "retrieve_policy",
            "human_review": "human_review",
        },
    )

    # Linear path
    g.add_edge("retrieve_policy", "decide")
    g.add_edge("decide", "draft")
    g.add_edge("draft", END)

    # Human review terminates the run
    g.add_edge("human_review", END)

    return g.compile()


@lru_cache
def get_graph():
    return _build_graph()