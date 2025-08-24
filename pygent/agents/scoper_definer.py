from pydantic_ai import Agent

from pygent.core.config import REASONER_LLM_MODEL

scope_definer_agent = Agent(
    REASONER_LLM_MODEL,
    system_prompt='You are an expert at coding AI agents with Pydantic AI and defining the scope for doing so.',
)
