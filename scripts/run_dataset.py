"""Run the sample-ticket dataset through the graph and report accuracy.

Uses an in-memory checkpointer so this script never touches the dev DB.
Interrupted runs are counted separately — they aren't wrong, they just need
a human decision.
"""
import asyncio
import json
import uuid
from pathlib import Path

try:
    from langgraph.checkpoint.memory import InMemorySaver
except ImportError:
    from langgraph.checkpoint.memory import MemorySaver as InMemorySaver

from app.graph.workflow import build_graph


async def main():
    dataset_path = Path("data/sample_tickets.json")
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path}")
        return

    tickets = json.loads(dataset_path.read_text())
    graph = build_graph().compile(checkpointer=InMemorySaver())

    correct = 0
    interrupted = 0
    print(f"Running {len(tickets)} tickets...\n")

    for t in tickets:
        run_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": run_id}}
        try:
            result = await graph.ainvoke(
                {"ticket_text": t["text"], "trace": []}, config=config
            )
        except Exception as e:
            print(f"  ✗ #{t['id']:>2} error: {type(e).__name__}: {e}")
            continue

        if "__interrupt__" in result and result["__interrupt__"]:
            interrupted += 1
            print(f"  ⏸  #{t['id']:>2} interrupted → review needed ({t['text'][:45]!r})")
            continue

        got = result.get("category", "?")
        want = t["expected_category"]
        ok = got == want
        correct += ok
        mark = "✓" if ok else "✗"
        print(f"  {mark} #{t['id']:>2} got={got:<10} want={want:<10} {t['text'][:50]!r}")

    answered = len(tickets) - interrupted
    print()
    print(f"Category accuracy (of answered runs): {correct}/{answered}")
    print(f"Paused for human review:               {interrupted}/{len(tickets)}")


if __name__ == "__main__":
    asyncio.run(main())