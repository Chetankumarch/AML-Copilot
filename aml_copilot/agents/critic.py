"""Critic Agent — validates SAR drafts against FinCEN filing requirements."""

from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm


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
The user message will contain a SAR draft with these sections:
- subject_info
- suspicious_activity
- supporting_evidence
- risk_assessment
- recommended_action

Along with the original triage result and evidence bundle for cross-referencing.

## Validation Checklist
Review the SAR draft against these criteria:

1. **Subject Identification**: Does subject_info clearly identify the accounts
   involved, transaction type, and amount?

2. **Activity Description**: Does suspicious_activity explain what triggered
   the alert? Does it reference specific risk flags?

3. **Evidence Citation**: Does supporting_evidence cite specific data from the
   evidence bundle (sanctions list names, match scores, case IDs, dates)?
   Flag any claims not supported by the evidence.

4. **Risk Justification**: Does risk_assessment state the score and level?
   Is the justification consistent with the flags and evidence?

5. **Action Appropriateness**: Is the recommended_action appropriate for the
   risk level? (CRITICAL=immediate filing, HIGH=filing with review,
   MEDIUM=monitoring, LOW=no action)

## Verdict Rules
- **PASS**: All 5 sections present and substantive (not just placeholders),
  no unsupported claims, action matches risk level
- **FAIL**: Any section missing/empty, unsupported claims found, or
  action inappropriate for risk level

## Output Format
Respond with ONLY valid JSON:
{
  "verdict": "PASS or FAIL",
  "completeness_score": <0-100>,
  "missing_elements": ["<list of missing items, empty if none>"],
  "unsupported_claims": ["<list of unsupported claims, empty if none>"],
  "revision_instructions": "<specific revision instructions, empty string if PASS>"
}
"""


critic_agent = Agent(
    model=LiteLlm(model="ollama/llama3.2"),
    name="critic_agent",
    description="Validates SAR drafts against FinCEN filing requirements.",
    instruction=CRITIC_PROMPT,
    output_schema=CriticFeedback,
    output_key="critic_feedback",
)
