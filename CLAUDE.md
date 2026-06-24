# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run all tests
python -m pytest tests/ -q

# Run a single test file
python -m pytest tests/test_scoring.py -q

# Run a single test class or method
python -m pytest tests/test_scoring.py::TestHighRiskTransfer::test_score_is_critical -q

# Interactive UI (requires Ollama running)
adk web aml_copilot

# Batch process N transactions from PaySim dataset
python run_batch.py 10

# Lint
ruff check .
```

## Architecture

This is a multi-agent AML (Anti-Money Laundering) investigation co-pilot built on **Google ADK** (Agent Development Kit), using **Ollama/llama3.2** (3B) as the local LLM via ADK's `LiteLlm` wrapper.

### Current state: M1 (Triage Agent only)

The pipeline has one working agent. Agents for evidence gathering (M2), SAR narrative drafting (M3), critic validation (M4), and the full orchestrated graph (M5) are placeholder files.

### Agent → Tool → Output flow

`aml_copilot/agent.py` exports `root_agent` — the ADK entrypoint used by `adk web` and `adk run`. Currently this is just the triage agent.

**Triage agent** (`aml_copilot/agents/triage.py`): receives a PaySim transaction as text, calls the `compute_risk_score` tool exactly once, then returns structured JSON matching the `TriageOutput` Pydantic schema. The result is stored in `session.state["triage_result"]` via `output_key` for downstream agents.

**Scoring tool** (`aml_copilot/tools/scoring.py`): pure deterministic Python — no LLM. Applies 5 rule-based checks (large transfer, balance drain, empty destination, overdraft, round number) and returns `{risk_score, risk_level, flags}`.

### Ollama/llama3.2 callback workaround

llama3.2 (3B) cannot handle ADK sending `tools` and `response_format` (from `output_schema`) simultaneously — the JSON schema constraint blocks tool-call token emission. Two callbacks in `triage.py` solve this:

- `before_model_callback`: on the first LLM call, clears `response_schema` so the model can call the tool. On the second call (after tool ran), clears `tools` so `response_schema` enforces structured output.
- `after_tool_callback`: sets a state flag (`_risk_score_computed`) that the before callback reads. The flag is reset after consumption so subsequent transactions in the same session get fresh tool calls.

This workaround is unnecessary with larger models (8B+) that handle both simultaneously, but llama3.2 is used because the dev machine has 8GB RAM.

### Batch runner

`run_batch.py` uses ADK's `InMemoryRunner` (async) to loop through the PaySim CSV without needing `adk web`. The dataset (~6.3M rows) is downloaded via `kagglehub` to `~/.cache/kagglehub/datasets/ealaxi/paysim1/`.

## Autonomous work plan

When running autonomously (via /loop), work through these milestones in order. Each milestone should be committed when complete with tests passing.

### M2: Evidence Gathering Agent
- Create tools in `aml_copilot/tools/` for: transaction history lookup, sanctions list check, prior case search (use mock/synthetic data)
- Build `evidence_agent` in `aml_copilot/agents/evidence.py` that reads `session.state["triage_result"]` and runs fan-out searches
- Store output in `session.state["evidence_bundle"]` via `output_key`
- Apply the same Ollama callback workaround from triage if the agent uses tools + output_schema
- Write tests in `tests/test_evidence_agent.py`

### M3: Narrative Agent
- Build `narrative_agent` in `aml_copilot/agents/narrative.py` that reads triage result + evidence bundle from session state
- Drafts SAR-style report (Subject Info, Suspicious Activity Description, Supporting Evidence) grounded in FinCEN BSA guidance
- Store output in `session.state["sar_draft"]` via `output_key`
- Write tests in `tests/test_narrative_agent.py`

### M4: Critic Agent
- Build `critic_agent` in `aml_copilot/agents/critic.py` that validates the SAR draft
- Checks completeness against FinCEN SAR filing checklist, unsupported claims, missing fields
- Returns pass/fail with revision instructions
- Store output in `session.state["critic_feedback"]` via `output_key`
- Write tests in `tests/test_critic_agent.py`

### Quality gate — required before each push

Each milestone is a separate push to `origin/main`. Do NOT push multiple milestones together. Before pushing any milestone:

1. **Tests**: Run `python -m pytest tests/ -q` — ALL tests must pass (not just the new ones)
2. **Verify**: Run the agent end-to-end via `InMemoryRunner` with real PaySim transactions. Confirm the tool is called, output matches the Pydantic schema, and `session.state` contains the expected keys
3. **Edge cases**: Test with at least one low-risk and one high-risk transaction. Verify the agent handles both correctly
4. **Integration**: Wire the new agent into `aml_copilot/agent.py` and confirm existing agents still work
5. **No regressions**: Run `python run_batch.py 5` to verify the full pipeline still works end-to-end
6. **Commit**: Use a descriptive commit message (`feat: M2 evidence gathering agent — ...`)
7. **Push**: `git push origin main` — only after all above checks pass
8. **Mark done**: Update this section to mark the milestone complete

Do NOT commit or push code that is incomplete, untested, or has failing tests. Production grade means it works reliably, not just on the happy path.

## ADK conventions

- ADK calls `after_tool_callback` with **keyword arguments**: `tool`, `args`, `tool_context`, `tool_response`. Parameter names must match exactly.
- `before_model_callback` receives `(callback_context, llm_request)` — positional.
- `InMemoryRunner.session_service.create_session()` is async — must be awaited.
- ADK's `can_use_output_schema_with_tools()` returns `True` for all `LiteLlm` models, which is incorrect for Ollama. The callbacks above work around this.
