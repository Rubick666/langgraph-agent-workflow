import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.llm import llm
from app.graph.runtime import close_graph, init_graph
from app.routers import health, workflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Ensure the data directory exists
    db_dir = os.path.dirname(settings.database_path) or "."
    os.makedirs(db_dir, exist_ok=True)

    # 2. Initialize the graph + checkpointer
    await init_graph(settings.database_path)
    print(f"Graph compiled; checkpointer writing to {settings.database_path}")

    # 3. Warm up the LLM
    try:
        await llm.ainvoke("hello")
        print("LLM warmup complete.")
    except Exception as e:
        print(f"LLM warmup failed (will retry on first request): {e}")

    yield

    # Shutdown
    await close_graph()
    print("SQLite checkpointer closed.")


app = FastAPI(
    title="Triage Workflow API",
    version="0.1.0",
    description="LangGraph-based customer-support triage workflow with human-in-the-loop",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(workflow.router)


@app.get("/")
async def root():
    return {"service": "langgraph-agent-workflow"}