from fastapi import APIRouter

from app.graph.workflow import get_graph
from app.schemas.workflow import RunRequest, RunResponse

router = APIRouter(prefix="/workflow", tags=["workflow"])


@router.post("/run", response_model=RunResponse)
async def run_workflow(request: RunRequest):
    graph = get_graph()
    result = await graph.ainvoke({"ticket_text": request.ticket_text, "trace": []})

    return RunResponse(
        category=result.get("category", "other"),
        is_confident=result.get("is_confident", False),
        trace=result.get("trace", []),
        policy_reference=result.get("policy_reference"),
        decision=result.get("decision"),
        draft_response=result.get("draft_response"),
    )