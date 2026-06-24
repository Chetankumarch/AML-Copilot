"""Configuration tests for the Critic Agent."""

from google.adk.agents import Agent

from aml_copilot.agents.critic import critic_agent, CriticFeedback


class TestCriticAgentConfiguration:
    def test_agent_is_adk_agent(self):
        assert isinstance(critic_agent, Agent)

    def test_agent_name(self):
        assert critic_agent.name == "critic_agent"

    def test_no_tools(self):
        assert len(critic_agent.tools) == 0

    def test_output_key_is_set(self):
        assert critic_agent.output_key == "critic_feedback"

    def test_output_schema_is_set(self):
        assert critic_agent.output_schema == CriticFeedback

    def test_instruction_references_checklist(self):
        assert "Subject Identification" in critic_agent.instruction
        assert "Activity Description" in critic_agent.instruction
        assert "Evidence Citation" in critic_agent.instruction
        assert "Risk Justification" in critic_agent.instruction
        assert "Action Appropriateness" in critic_agent.instruction

    def test_instruction_references_verdicts(self):
        assert "PASS" in critic_agent.instruction
        assert "FAIL" in critic_agent.instruction

    def test_no_callbacks_needed(self):
        assert critic_agent.before_model_callback is None
        assert critic_agent.after_tool_callback is None


class TestCriticFeedbackSchema:
    def test_has_required_fields(self):
        fields = CriticFeedback.model_fields
        assert "verdict" in fields
        assert "completeness_score" in fields
        assert "missing_elements" in fields
        assert "unsupported_claims" in fields
        assert "revision_instructions" in fields

    def test_pass_verdict(self):
        feedback = CriticFeedback(
            verdict="PASS",
            completeness_score=95,
            missing_elements=[],
            unsupported_claims=[],
            revision_instructions="",
        )
        assert feedback.verdict == "PASS"
        assert feedback.completeness_score == 95

    def test_fail_verdict(self):
        feedback = CriticFeedback(
            verdict="FAIL",
            completeness_score=40,
            missing_elements=["Subject account IDs not specified"],
            unsupported_claims=["Claims sanctions match without evidence"],
            revision_instructions="Add specific account IDs and cite sanctions data.",
        )
        assert feedback.verdict == "FAIL"
        assert len(feedback.missing_elements) == 1
        assert len(feedback.unsupported_claims) == 1
