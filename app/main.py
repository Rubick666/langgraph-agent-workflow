from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import health, workflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warmup: trigger the first model load so the first real request is fast
    from app.core.llm import llm
    try:
        await llm.ainvoke("hello")
        print("LLM warmup complete.")
    except Exception as e:
        print(f"LLM warmup failed (will retry on first request): {e}")
    yield


app = FastAPI(
    title="Triage Workflow API",
    version="0.1.0",
    description="LangGraph-based customer-support triage workflow",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(workflow.router)


@app.get("/")
async def root():
    return {"service": "langgraph-agent-workflow"}