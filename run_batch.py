"""Batch runner — feeds PaySim transactions through the triage→evidence→narrative pipeline."""

import asyncio
import csv
import json
import sys

from google.adk.runners import InMemoryRunner
from google.genai import types

from aml_copilot.agents.triage import triage_agent
from aml_copilot.agents.evidence import evidence_agent
from aml_copilot.agents.narrative import narrative_agent

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


async def run_agent(runner, user_id, session_id, message_text):
    """Run a single agent and return its final text response."""
    message = types.Content(
        role="user",
        parts=[types.Part(text=message_text)],
    )
    result_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=message,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            text = "".join(p.text for p in event.content.parts if p.text)
            if text.strip():
                result_text = text
    return result_text


async def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10

    triage_runner = InMemoryRunner(agent=triage_agent, app_name="aml_triage")
    evidence_runner = InMemoryRunner(agent=evidence_agent, app_name="aml_evidence")
    narrative_runner = InMemoryRunner(agent=narrative_agent, app_name="aml_narrative")

    with open(PAYSIM_CSV, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break

            tx_text = format_transaction(row)
            session_id = f"tx_{i}"

            await triage_runner.session_service.create_session(
                app_name="aml_triage", user_id="batch", session_id=session_id
            )

            # Stage 1: Triage
            print(f"\n{'='*60}")
            print(f"Transaction {i+1}: {tx_text}")
            print("-" * 60)

            triage_text = await run_agent(
                triage_runner, "batch", session_id, tx_text
            )

            try:
                triage_result = json.loads(triage_text)
                print("TRIAGE:")
                print(json.dumps(triage_result, indent=2))
            except json.JSONDecodeError:
                print(f"TRIAGE (raw): {triage_text}")
                continue

            # Stage 2: Evidence (only for MEDIUM+ risk)
            risk_score = triage_result.get("risk_score", 0)
            if risk_score < 26:
                print(f"\nSkipping evidence & narrative (risk_score={risk_score} < 26)")
                continue

            await evidence_runner.session_service.create_session(
                app_name="aml_evidence", user_id="batch", session_id=session_id
            )
            evidence_prompt = (
                f"Gather evidence for: nameOrig={row['nameOrig']}, "
                f"nameDest={row['nameDest']}"
            )
            evidence_text = await run_agent(
                evidence_runner, "batch", session_id, evidence_prompt
            )
            try:
                evidence_result = json.loads(evidence_text)
                print("\nEVIDENCE:")
                print(json.dumps(evidence_result, indent=2))
            except json.JSONDecodeError:
                print(f"\nEVIDENCE (raw): {evidence_text}")
                continue

            # Stage 3: Narrative (SAR draft)
            await narrative_runner.session_service.create_session(
                app_name="aml_narrative", user_id="batch", session_id=session_id
            )
            narrative_prompt = (
                f"Draft a SAR for this transaction:\n"
                f"Transaction: {tx_text}\n"
                f"Triage: {json.dumps(triage_result)}\n"
                f"Evidence: {json.dumps(evidence_result)}"
            )
            narrative_text = await run_agent(
                narrative_runner, "batch", session_id, narrative_prompt
            )
            try:
                sar_draft = json.loads(narrative_text)
                print("\nSAR DRAFT:")
                print(json.dumps(sar_draft, indent=2))
            except json.JSONDecodeError:
                print(f"\nSAR DRAFT (raw): {narrative_text}")

    print(f"\n{'='*60}")
    print(f"Processed {min(limit, i+1)} transactions.")


if __name__ == "__main__":
    asyncio.run(main())
