"""Narrative Agent — drafts SAR-style reports from triage and evidence."""

from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm


class SARDraft(BaseModel):
    subject_info: str = Field(
        description="Subject identification: account IDs, transaction type, amount"
    )
    suspicious_activity: str = Field(
        description="Description of the suspicious activity and why it was flagged"
    )
    supporting_evidence: str = Field(
        description="Evidence from transaction history, sanctions, and prior cases"
    )
    risk_assessment: str = Field(
        description="Overall risk level and score with justification"
    )
    recommended_action: str = Field(
        description="Recommended next steps: file SAR, escalate, or dismiss"
    )


NARRATIVE_PROMPT = """\
You are an AML Narrative Writer. You draft Suspicious Activity Reports (SARs)
based on triage results and evidence bundles provided in the user's message.

## Input
The user message will contain:
- Transaction details (type, amount, accounts)
- Triage result (risk_score, risk_level, flags)
- Evidence bundle (transaction history, sanctions hits, prior cases)

## SAR Structure
Write a concise report covering these sections:

1. **Subject Information**: Identify the accounts involved, transaction type,
   and amount. State the origin and destination accounts clearly.

2. **Suspicious Activity Description**: Explain what triggered the alert.
   Reference the specific risk flags from triage. Describe the pattern
   (e.g., balance drain, large transfer, structuring).

3. **Supporting Evidence**: Cite specific findings from the evidence bundle.
   Mention sanctions matches (list name, entity, match score), prior SAR cases
   (case ID, date, outcome), and relevant transaction history patterns.

4. **Risk Assessment**: State the risk score and level. Justify based on the
   combination of flags and evidence.

5. **Recommended Action**: Based on the risk level and evidence:
   - CRITICAL (76-100): Recommend immediate SAR filing
   - HIGH (51-75): Recommend SAR filing with additional review
   - MEDIUM (26-50): Recommend enhanced monitoring
   - LOW (0-25): Recommend no further action

## Output Format
Respond with ONLY valid JSON matching the required schema. Each field should
contain 2-4 sentences of clear, factual narrative. Do not include markdown
formatting within the JSON string values.
"""


narrative_agent = Agent(
    model=LiteLlm(model="ollama/llama3.2"),
    name="narrative_agent",
    description="Drafts SAR-style reports from triage and evidence data.",
    instruction=NARRATIVE_PROMPT,
    output_schema=SARDraft,
    output_key="sar_draft",
)
