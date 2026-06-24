"""Triage Agent — scores PaySim transactions for fraud risk."""

from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from aml_copilot.tools.scoring import compute_risk_score


class TriageOutput(BaseModel):
    risk_score: int = Field(description="Risk score from 0-100")
    risk_level: str = Field(description="CRITICAL, HIGH, MEDIUM, or LOW")
    reason: str = Field(description="1-2 sentence explanation referencing the flags")
    flags: list[str] = Field(description="List of triggered risk flags")


TRIAGE_PROMPT = """\
You are an AML Triage Analyst. You receive a single PaySim transaction and must
assess its fraud/money-laundering risk.

## Transaction Fields
- step: time step (1 step = 1 hour of simulation)
- type: CASH_IN | CASH_OUT | DEBIT | PAYMENT | TRANSFER
- amount: transaction amount
- nameOrig / nameDest: origin and destination account IDs
- oldbalanceOrg / newbalanceOrig: origin account balance before/after
- oldbalanceDest / newbalanceDest: destination account balance before/after

## Workflow
1. Extract the transaction fields from the user's message.
2. Call `compute_risk_score` EXACTLY ONCE with ALL transaction fields.
3. After receiving the tool result, immediately produce your final response
   using the returned risk_score, risk_level, and flags. Do NOT call the tool
   again.

## Output Format
Respond with ONLY valid JSON:
{
  "risk_score": <score from tool>,
  "risk_level": "<level from tool>",
  "reason": "<1-2 sentence plain-language explanation referencing the specific flags>",
  "flags": [<flags list from tool>]
}
"""


def _strip_tools_after_first_call(callback_context, llm_request):
    """Manage tools and output schema per LLM call.

    Call 1 (tool call): tools present, suppress response_schema so Ollama
    doesn't receive both tools + response_format simultaneously.
    Call 2 (final answer): strip tools, keep response_schema so Ollama
    enforces the JSON output structure.
    """
    if callback_context.state.get("_risk_score_computed"):
        llm_request.config.tools = []
        callback_context.state["_risk_score_computed"] = False
    else:
        llm_request.config.response_schema = None
        llm_request.config.response_mime_type = None
    return None


def _mark_tool_called(tool, args, tool_context, tool_response):
    """Set state flag after compute_risk_score executes."""
    tool_context.state["_risk_score_computed"] = True


triage_agent = Agent(
    model=LiteLlm(model="ollama/llama3.2"),
    name="triage_agent",
    description="Scores a PaySim transaction for AML/fraud risk (0-100).",
    instruction=TRIAGE_PROMPT,
    tools=[compute_risk_score],
    output_schema=TriageOutput,
    output_key="triage_result",
    before_model_callback=_strip_tools_after_first_call,
    after_tool_callback=_mark_tool_called,
)
