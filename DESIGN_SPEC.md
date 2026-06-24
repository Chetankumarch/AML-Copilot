# AML-Copilot — Design Specification

## Overview

AML-Copilot is a multi-agent Anti-Money Laundering investigation co-pilot built on Google's Agent Development Kit (ADK). It automates the triage-to-SAR pipeline for PaySim-style transaction data, combining AI-driven risk scoring with human-in-the-loop approval.

## Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────────┐
│   Ingest     │────▶│  Triage Agent   │────▶│ Evidence Gatherer │
│ (PaySim tx)  │     │ (risk scoring)  │     │  (fan-out search) │
└─────────────┘     └─────────────────┘     └──────────────────┘
                                                      │
                          ┌───────────────────────────┘
                          ▼
                  ┌──────────────────┐     ┌──────────────────┐
                  │ Narrative Agent  │────▶│  Critic Agent    │
                  │ (SAR drafting)   │     │ (validation)     │
                  └──────────────────┘     └──────────────────┘
                                                      │
                                                      ▼
                                           ┌──────────────────┐
                                           │  Human Approval  │
                                           │  Gate (HITL)     │
                                           └──────────────────┘
```

## Pipeline Stages

### 1. Triage Agent
- **Input:** Transaction dict matching PaySim schema (`step`, `type`, `amount`, `nameOrig`, `oldbalanceOrg`, `newbalanceOrig`, `nameDest`, `oldbalanceDest`, `newbalanceDest`)
- **Output:** Risk score (0–100) + plain-language reason
- **Logic:** Heuristic + LLM hybrid — flags balance mismatches, large CASH_OUT/TRANSFER patterns, velocity anomalies

### 2. Evidence Gathering (Fan-out)
- **Transaction history lookup** — prior txns for origin/destination accounts
- **Sanctions list check** — OFAC/UN sanctions screening
- **Prior case search** — match against previously filed SARs
- Runs in parallel; results aggregated into an evidence bundle

### 3. Narrative Agent
- Drafts SAR-style report grounded in FinCEN BSA guidance
- Sections: Subject Information, Suspicious Activity Description, Supporting Evidence
- Cites specific transaction IDs and evidence sources

### 4. Critic Agent
- Validates completeness against FinCEN SAR filing checklist
- Checks for unsupported claims, missing fields, logical inconsistencies
- Returns pass/fail with specific revision instructions

### 5. Human-in-the-Loop Approval Gate
- Surfaces the draft SAR + critic feedback to a human reviewer
- Reviewer can approve, reject, or request revisions
- Only approved reports proceed to "filed" status

## Tech Stack

| Component        | Technology              |
|-----------------|------------------------|
| Orchestration   | Google ADK (Workflow Runtime) |
| LLM             | Gemini (via ADK)        |
| Data Schema     | PaySim synthetic dataset |
| Language        | Python 3.11+            |
| UI              | ADK Playground (localhost:8080) |

## PaySim Transaction Schema

```python
{
    "step": int,           # time step (1 step = 1 hour)
    "type": str,           # CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER
    "amount": float,       # transaction amount
    "nameOrig": str,       # origin account
    "oldbalanceOrg": float,
    "newbalanceOrig": float,
    "nameDest": str,       # destination account
    "oldbalanceDest": float,
    "newbalanceDest": float,
    "isFraud": int,        # ground truth label (0/1)
    "isFlaggedFraud": int  # naive rule-based flag
}
```

## Milestones

1. **M1:** Triage Agent — single node, risk scores PaySim transactions ← *start here*
2. **M2:** Evidence Gathering — fan-out tools with mock data
3. **M3:** Narrative Agent — SAR draft generation
4. **M4:** Critic Agent — validation loop
5. **M5:** Full graph + HITL gate
6. **M6:** Evaluation harness (precision/recall on PaySim labels)
