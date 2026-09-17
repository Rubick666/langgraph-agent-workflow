from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.graph.nodes import classify_node
from app.graph.state import TicketState


def _build_graph():
    g = StateGraph(TicketState)
    g.add_node("classify", classify_node)

    g.add_edge(START, "classify")
    g.add_edge("classify", END)

    return g.compile()


@lru_cache
def get_graph():
    """Compile the graph once and reuse it (compilation is expensive)."""
    return _build_graph()