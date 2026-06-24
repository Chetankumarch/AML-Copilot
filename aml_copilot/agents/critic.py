"""Critic Agent — validates SAR drafts against FinCEN filing requirements."""

from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from aml_copilot.tools.validation import validate_sar_draft


class CriticFeedback(BaseModel):
    verdict: str = Field(description="PASS or FAIL")
    completeness_score: int = Field(
        description="Score from 0-100 for how complete the SAR draft is"
    )
    missing_elements: list[str] = Field(
        description="List of missing or incomplete SAR elements"
    )
    unsupported_claims: list[str] = Field(
        description="Claims in the draft not backed by evidence"
    )
    revision_instructions: str = Field(
        description="Specific instructions for improving the draft, empty if PASS"
    )


CRITIC_PROMPT = """\
You are an AML Compliance Reviewer. You validate SAR (Suspicious Activity Report)
drafts against FinCEN BSA filing requirements.

## Input
The user message will contain:
- A SAR draft with fields: subject_info, suspicious_activity, supporting_evidence,
  risk_assessment, recommended_action
- The original triage result (risk_score, risk_level, flags)
- The evidence bundle (sanctions_hits, prior_cases)

## Workflow
1. Extract the SAR draft fields, triage result, and evidence data from the message.
2. Call `validate_sar_draft` EXACTLY ONCE with ALL required parameters:
   - sar_subject_info, sar_suspicious_activity, sar_supporting_evidence,
     sar_risk_assessment, sar_recommended_action (from the SAR draft)
   - triage_risk_score, triage_risk_level, triage_flags (from triage result)
   - evidence_sanctions_hits, evidence_prior_cases (from evidence bundle)
3. After receiving the tool result, produce your final response using the
   returned verdict, completeness_score, missing_elements, unsupported_claims,
   and revision_instructions. Do NOT call the tool again.

## Output Format
Respond with ONLY valid JSON:
{
  "verdict": "<verdict from tool>",
  "completeness_score": <score from tool>,
  "missing_elements": [<missing_elements from tool>],
  "unsupported_claims": [<unsupported_claims from tool>],
  "revision_instructions": "<revision_instructions from tool>"
}
"""


def _strip_tools_after_first_call(callback_context, llm_request):
    """Toggle tools vs response_schema per LLM call."""
    if callback_context.state.get("_validation_done"):
        llm_request.config.tools = []
        callback_context.state["_validation_done"] = False
    else:
        llm_request.config.response_schema = None
        llm_request.config.response_mime_type = None
    return None


def _mark_tool_called(tool, args, tool_context, tool_response):
    """Set state flag after validate_sar_draft executes."""
    tool_context.state["_validation_done"] = True


critic_agent = Agent(
    model=LiteLlm(model="ollama/llama3.2"),
    name="critic_agent",
    description="Validates SAR drafts against FinCEN filing requirements.",
    instruction=CRITIC_PROMPT,
    tools=[validate_sar_draft],
    output_schema=CriticFeedback,
    output_key="critic_feedback",
    before_model_callback=_strip_tools_after_first_call,
    after_tool_callback=_mark_tool_called,
)
