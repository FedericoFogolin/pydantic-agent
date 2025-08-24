from __future__ import annotations

import logfire
from pydantic_ai import Agent

from pygent.core.config import PRIMARY_LLM_MODEL

from .prompt_refiner_prompt import prompt_refiner_prompt

logfire.configure()

prompt_refiner_agent = Agent(PRIMARY_LLM_MODEL, system_prompt=prompt_refiner_prompt)
