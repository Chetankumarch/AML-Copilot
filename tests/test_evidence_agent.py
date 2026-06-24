"""Configuration tests for the Evidence Gathering Agent."""

from google.adk.agents import Agent

from aml_copilot.agents.evidence import evidence_agent, EvidenceOutput


class TestEvidenceAgentConfiguration:
    def test_agent_is_adk_agent(self):
        assert isinstance(evidence_agent, Agent)

    def test_agent_name(self):
        assert evidence_agent.name == "evidence_agent"

    def test_agent_has_one_tool(self):
        assert len(evidence_agent.tools) == 1

    def test_instruction_references_tool(self):
        assert "gather_evidence" in evidence_agent.instruction

    def test_output_key_is_set(self):
        assert evidence_agent.output_key == "evidence_bundle"

    def test_output_schema_is_set(self):
        assert evidence_agent.output_schema == EvidenceOutput

    def test_before_model_callback_is_set(self):
        assert evidence_agent.before_model_callback is not None

    def test_after_tool_callback_is_set(self):
        assert evidence_agent.after_tool_callback is not None


class TestEvidenceOutputSchema:
    def test_has_required_fields(self):
        fields = EvidenceOutput.model_fields
        assert "origin_account" in fields
        assert "destination_account" in fields
        assert "origin_history_summary" in fields
        assert "destination_history_summary" in fields
        assert "sanctions_hits" in fields
        assert "prior_cases" in fields
        assert "evidence_summary" in fields

    def test_schema_validates(self):
        output = EvidenceOutput(
            origin_account="C1",
            destination_account="C2",
            origin_history_summary="test",
            destination_history_summary="test",
            sanctions_hits=[],
            prior_cases=[],
            evidence_summary="test",
        )
        assert isinstance(output.sanctions_hits, list)
        assert isinstance(output.prior_cases, list)
