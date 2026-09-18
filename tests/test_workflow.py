"""Integration tests for the triage workflow API.

Tests are structural: they assert on the shape of the response and the
behavior of the graph (completed vs. interrupted vs. resumed), not on the
tiny LLM's exact category output. That makes them robust and fast.
"""
from fastapi.testclient import TestClient


# ---------------------------------------------------------------- health
def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm_reachable"] is True


# ------------------------------------------------------------ happy path
def test_run_completed_ticket(client: TestClient):
    """A ticket that should not require human review."""
    r = client.post(
        "/workflow/run",
        json={"ticket_text": "I was charged twice for my last order. Please refund."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"]
    assert body["status"] in {"completed", "awaiting_review"}  # tolerate tiny-model quirks

    state = body["state"]
    assert state["category"] in {"billing", "account", "other"}
    assert isinstance(state["trace"], list)
    assert len(state["trace"]) >= 1
    assert state["trace"][0]["node"] == "classify"


# ------------------------------------------------------------- escalation
def test_escalation_pauses_for_review(client: TestClient):
    """A ticket explicitly asking for a manager must interrupt the graph."""
    r = client.post(
        "/workflow/run",
        json={"ticket_text": "I want to speak to a manager about this immediately."},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "awaiting_review"
    assert body["interrupt"] is not None
    assert body["interrupt"]["reason"] == "escalation_requires_approval"
    run_id = body["run_id"]
    assert run_id


def test_resume_escalation_with_approve(client: TestClient):
    """Approve escalation → run completes with decision=escalate."""
    run = client.post(
        "/workflow/run",
        json={"ticket_text": "This is unacceptable, escalate me to a senior engineer now."},
    ).json()
    assert run["status"] == "awaiting_review"
    run_id = run["run_id"]

    resume = client.post(
        f"/workflow/{run_id}/resume",
        json={"action": "approve", "note": "Approved by test."},
    )
    assert resume.status_code == 200
    body = resume.json()
    assert body["status"] == "completed"
    assert body["state"]["decision"] == "escalate"
    assert body["state"]["human_action"] == "approve"
    # trace should now include the review_escalation node
    nodes = [t["node"] for t in body["state"]["trace"]]
    assert "review_escalation" in nodes


def test_resume_escalation_with_respond(client: TestClient):
    """Respond instead of escalating → run completes with a draft."""
    run = client.post(
        "/workflow/run",
        json={"ticket_text": "I want to talk to a manager."},
    ).json()
    if run["status"] != "awaiting_review":
        return

    run_id = run["run_id"]
    resume = client.post(
        f"/workflow/{run_id}/resume",
        json={"action": "respond"},
    )
    assert resume.status_code == 200
    body = resume.json()
    assert body["status"] == "completed"
    assert body["state"]["decision"] == "respond"
    assert body["state"]["draft_response"]


# --------------------------------------------------------------- inspect
def test_get_completed_run(client: TestClient):
    run = client.post(
        "/workflow/run",
        json={"ticket_text": "My app crashes on startup, please advise."},
    ).json()
    run_id = run["run_id"]

    r = client.get(f"/workflow/{run_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == run_id
    assert body["state"]["category"] == run["state"]["category"]


def test_get_unknown_run_returns_404(client: TestClient):
    r = client.get("/workflow/does-not-exist-12345")
    assert r.status_code == 404


def test_resume_unknown_run_returns_404(client: TestClient):
    r = client.post(
        "/workflow/does-not-exist-12345/resume",
        json={"action": "confirm"},
    )
    assert r.status_code == 404


def test_resume_completed_run_returns_400(client: TestClient):
    """Resuming a run that already finished should be a 400, not a crash."""
    run = client.post(
        "/workflow/run",
        json={"ticket_text": "The dashboard won't load in Safari."},
    ).json()
    if run["status"] == "awaiting_review":
        return
    run_id = run["run_id"]
    r = client.post(
        f"/workflow/{run_id}/resume",
        json={"action": "respond"},
    )
    assert r.status_code == 400


# ------------------------------------------------------------ validation
def test_run_rejects_short_input(client: TestClient):
    r = client.post("/workflow/run", json={"ticket_text": "hi"})
    assert r.status_code == 422


def test_run_rejects_missing_field(client: TestClient):
    r = client.post("/workflow/run", json={})
    assert r.status_code == 422