"""Configuration tests for the Narrative Agent."""

from google.adk.agents import Agent

from aml_copilot.agents.narrative import narrative_agent, SARDraft


class TestNarrativeAgentConfiguration:
    def test_agent_is_adk_agent(self):
        assert isinstance(narrative_agent, Agent)

    def test_agent_name(self):
        assert narrative_agent.name == "narrative_agent"

    def test_no_tools(self):
        assert len(narrative_agent.tools) == 0

    def test_output_key_is_set(self):
        assert narrative_agent.output_key == "sar_draft"

    def test_output_schema_is_set(self):
        assert narrative_agent.output_schema == SARDraft

    def test_instruction_references_risk_levels(self):
        assert "CRITICAL" in narrative_agent.instruction
        assert "HIGH" in narrative_agent.instruction
        assert "MEDIUM" in narrative_agent.instruction
        assert "LOW" in narrative_agent.instruction

    def test_no_callbacks_needed(self):
        assert narrative_agent.before_model_callback is None
        assert narrative_agent.after_tool_callback is None


class TestSARDraftSchema:
    def test_has_required_fields(self):
        fields = SARDraft.model_fields
        assert "subject_info" in fields
        assert "suspicious_activity" in fields
        assert "supporting_evidence" in fields
        assert "risk_assessment" in fields
        assert "recommended_action" in fields

    def test_schema_validates(self):
        draft = SARDraft(
            subject_info="Account C1234 transferred $4.5M to C5678.",
            suspicious_activity="Large transfer with balance drain.",
            supporting_evidence="OFAC-SDN match on origin account.",
            risk_assessment="CRITICAL (score 85).",
            recommended_action="Recommend immediate SAR filing.",
        )
        assert draft.subject_info.startswith("Account")
        assert "CRITICAL" in draft.risk_assessment
