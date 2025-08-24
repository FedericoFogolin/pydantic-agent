from pydantic_ai import Agent

from pygent.core.config import REASONER_LLM_MODEL
from pygent.prompts.reasoner import reasoner

cope_definer_agent = Agent(
    REASONER_LLM_MODEL,
    system_prompt=reasoner,
)
