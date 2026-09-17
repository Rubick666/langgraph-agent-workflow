import uuid

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from app.graph.runtime import get_graph
from app.schemas.workflow import (
    ResumeRequest,
    RunRequest,
    RunResponse,
    WorkflowState,
)

router = APIRouter(prefix="/workflow", tags=["workflow"])


def _extract_interrupt(result: dict) -> dict | None:
    """Normalise the `__interrupt__` key across langgraph versions."""
    interrupts = result.get("__interrupt__")
    if not interrupts:
        return None
    first = interrupts[0]
    if hasattr(first, "value"):
        return first.value
    if isinstance(first, dict):
        return first.get("value", first)
    return {"raw": str(first)}


def _format(run_id: str, result: dict) -> RunResponse:
    payload = _extract_interrupt(result)
    state_dict = {k: v for k, v in result.items() if not k.startswith("__")}
    return RunResponse(
        run_id=run_id,
        status="awaiting_review" if payload is not None else "completed",
        state=WorkflowState(**state_dict),
        interrupt=payload,
    )


@router.post("/run", response_model=RunResponse)
async def run_workflow(request: RunRequest):
    """Start a new run. Returns either the completed result or an interrupt to answer."""
    run_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": run_id}}
    graph = get_graph()

    result = await graph.ainvoke(
        {"ticket_text": request.ticket_text, "trace": []},
        config=config,
    )
    return _format(run_id, result)


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(run_id: str):
    """Inspect the current state of a run — its values, next nodes, and interrupt (if any)."""
    config = {"configurable": {"thread_id": run_id}}
    graph = get_graph()

    snapshot = await graph.aget_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Run not found")

    result = dict(snapshot.values)
    # If the run is paused at an interrupt, aget_state doesn't include __interrupt__.
    # Surface the pending task info so clients know review is expected.
    if snapshot.next:
        result["__pending_nodes__"] = list(snapshot.next)

    payload = None
    if snapshot.tasks:
        # The first task's `interrupts` field carries the payload we passed to interrupt()
        for task in snapshot.tasks:
            ints = getattr(task, "interrupts", None)
            if ints:
                first = ints[0]
                payload = getattr(first, "value", None) or {"raw": str(first)}
                break

    return _format(run_id, {**result, "__interrupt__": [type("I", (), {"value": payload})()] if payload else None})


@router.post("/{run_id}/resume", response_model=RunResponse)
async def resume_run(run_id: str, request: ResumeRequest):
    """Resume a paused run with a human decision."""
    config = {"configurable": {"thread_id": run_id}}
    graph = get_graph()

    snapshot = await graph.aget_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Run not found")
    if not snapshot.next:
        raise HTTPException(status_code=400, detail="Run is not awaiting review")

    payload = request.model_dump(exclude_none=True)
    result = await graph.ainvoke(Command(resume=payload), config=config)
    return _format(run_id, result)