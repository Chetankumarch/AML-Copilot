"""ADK entrypoint — exports the root agent for `adk web` / `adk run`.

For interactive use (adk web), root_agent is the triage agent.
For the full pipeline, use run_batch.py which runs agents sequentially.
"""

from aml_copilot.agents.triage import triage_agent

root_agent = triage_agent
