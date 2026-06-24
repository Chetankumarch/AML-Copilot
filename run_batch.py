"""Batch runner — feeds PaySim transactions to the triage agent in a loop."""

import asyncio
import csv
import json
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

from aml_copilot.agents.triage import triage_agent

PAYSIM_CSV = (
    "/Users/chetankumarch/.cache/kagglehub/datasets"
    "/ealaxi/paysim1/versions/2/PS_20174392719_1491204439457_log.csv"
)

TX_FIELDS = [
    "step", "type", "amount", "nameOrig",
    "oldbalanceOrg", "newbalanceOrig", "nameDest",
    "oldbalanceDest", "newbalanceDest",
]


def format_transaction(row: dict) -> str:
    return ", ".join(f"{k}={row[k]}" for k in TX_FIELDS)


async def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    runner = InMemoryRunner(agent=triage_agent, app_name="aml_copilot")
    user_id = "batch_user"
    session_id = "batch_session"

    await runner.session_service.create_session(
        app_name="aml_copilot", user_id=user_id, session_id=session_id
    )

    with open(PAYSIM_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break

            tx_text = format_transaction(row)
            print(f"\n{'='*60}")
            print(f"Transaction {i+1}: {tx_text}")
            print("-" * 60)

            message = types.Content(
                role="user",
                parts=[types.Part(text=tx_text)],
            )

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    text = "".join(
                        p.text for p in event.content.parts if p.text
                    )
                    if text.strip():
                        try:
                            result = json.loads(text)
                            print(json.dumps(result, indent=2))
                        except json.JSONDecodeError:
                            print(text)

    print(f"\n{'='*60}")
    print(f"Processed {min(limit, i+1)} transactions.")


if __name__ == "__main__":
    asyncio.run(main())
