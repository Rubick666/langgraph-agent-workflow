<<<<<<< HEAD
# Triage Workflow (langgraph-agent-workflow)

A LangGraph-based customer-support triage workflow.
Classifies a ticket → retrieves policy → decides → drafts a response.

## Quick Start

1. `docker-compose up --build`
2. Pull the model (one-time, ~400 MB):
   `docker-compose exec ollama ollama pull qwen2.5:0.5b`
3. Verify: `http://localhost:8000/health`
4. Docs: `http://localhost:8000/docs`

## API

`POST /workflow/run` with body `{"ticket_text": "..."}` — returns the classification.
=======
# langgraph-agent-workflow
>>>>>>> 645231e3a8d18606bf8ac0c2c2cb87988e737060
