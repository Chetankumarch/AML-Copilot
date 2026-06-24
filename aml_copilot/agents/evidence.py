"""Evidence Gathering Agent — fan-out search for supporting evidence."""

from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from aml_copilot.tools.evidence import gather_evidence


class EvidenceOutput(BaseModel):
    origin_account: str = Field(description="Origin account ID")
    destination_account: str = Field(description="Destination account ID")
    origin_history_summary: str = Field(
        description="Summary of origin account transaction history"
    )
    destination_history_summary: str = Field(
        description="Summary of destination account transaction history"
    )
    sanctions_hits: list[str] = Field(
        description="List of sanctions matches found, empty if none"
    )
    prior_cases: list[str] = Field(
        description="List of prior SAR case summaries, empty if none"
    )
    evidence_summary: str = Field(
        description="2-3 sentence overall evidence assessment"
    )


EVIDENCE_PROMPT = """\
You are an AML Evidence Analyst. You gather supporting evidence for a flagged
transaction by searching multiple data sources.

## Workflow
1. Extract the origin account (nameOrig) and destination account (nameDest)
   from the user's message.
2. Call `gather_evidence` EXACTLY ONCE with nameOrig and nameDest.
3. After receiving the tool result, produce your final evidence summary.
   Do NOT call the tool again.

## Output Format
Respond with ONLY valid JSON:
{
  "origin_account": "<nameOrig>",
  "destination_account": "<nameDest>",
  "origin_history_summary": "<summary of origin account's recent transactions>",
  "destination_history_summary": "<summary of destination account's recent transactions>",
  "sanctions_hits": ["<sanctions match details, empty list if none>"],
  "prior_cases": ["<prior SAR case details, empty list if none>"],
  "evidence_summary": "<2-3 sentence overall assessment of evidence findings>"
}
"""


def _strip_tools_after_first_call(callback_context, llm_request):
    """Toggle tools vs response_schema per LLM call."""
    if callback_context.state.get("_evidence_gathered"):
        llm_request.config.tools = []
        callback_context.state["_evidence_gathered"] = False
    else:
        llm_request.config.response_schema = None
        llm_request.config.response_mime_type = None
    return None


def _mark_tool_called(tool, args, tool_context, tool_response):
    """Set state flag after gather_evidence executes."""
    tool_context.state["_evidence_gathered"] = True


evidence_agent = Agent(
    model=LiteLlm(model="ollama/llama3.2"),
    name="evidence_agent",
    description="Gathers supporting evidence for a flagged transaction.",
    instruction=EVIDENCE_PROMPT,
    tools=[gather_evidence],
    output_schema=EvidenceOutput,
    output_key="evidence_bundle",
    before_model_callback=_strip_tools_after_first_call,
    after_tool_callback=_mark_tool_called,
)
