from __future__ import annotations

import logfire
import os
from dotenv import load_dotenv

from pydantic_ai import Agent

from ..prompts import prompt_refiner

load_dotenv()
logfire.configure()

primary_llm_model = os.getenv("PRIMARY_MODEL", "gpt-4o")

prompt_refiner = Agent(primary_llm_model, system_prompt=prompt_refiner)
