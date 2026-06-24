"""Configuration tests for the Triage Agent."""

from google.adk.agents import Agent

from aml_copilot.agents.triage import triage_agent, TriageOutput


class TestTriageAgentConfiguration:
    def test_agent_is_adk_agent(self):
        assert isinstance(triage_agent, Agent)

    def test_agent_name(self):
        assert triage_agent.name == "triage_agent"

    def test_agent_has_scoring_tool(self):
        assert len(triage_agent.tools) == 1

    def test_instruction_references_tool(self):
        assert "compute_risk_score" in triage_agent.instruction

    def test_before_model_callback_is_set(self):
        assert triage_agent.before_model_callback is not None

    def test_after_tool_callback_is_set(self):
        assert triage_agent.after_tool_callback is not None

    def test_output_key_is_set(self):
        assert triage_agent.output_key == "triage_result"

    def test_output_schema_is_set(self):
        assert triage_agent.output_schema == TriageOutput

    def test_output_schema_has_required_fields(self):
        fields = TriageOutput.model_fields
        assert "risk_score" in fields
        assert "risk_level" in fields
        assert "reason" in fields
        assert "flags" in fields
