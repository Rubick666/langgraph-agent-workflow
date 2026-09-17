from typing import Optional

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.graph.workflow import build_graph

_graph = None
_saver: Optional[AsyncSqliteSaver] = None
_conn: Optional[aiosqlite.Connection] = None


async def init_graph(database_path: str) -> None:
    """Open the SQLite connection, build the saver, and compile the graph."""
    global _graph, _saver, _conn
    if _graph is not None:
        return
    _conn = await aiosqlite.connect(database_path)
    _saver = AsyncSqliteSaver(_conn)
    _graph = build_graph().compile(checkpointer=_saver)


async def close_graph() -> None:
    global _conn, _graph, _saver
    if _conn is not None:
        await _conn.close()
    _conn = None
    _saver = None
    _graph = None


def get_graph():
    if _graph is None:
        raise RuntimeError("Graph not initialized — did startup run?")
    return _graph