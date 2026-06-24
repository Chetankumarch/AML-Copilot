"""ADK entrypoint — exports the root agent for `adk web` / `adk run`."""

from aml_copilot.agents.triage import triage_agent

root_agent = triage_agent
