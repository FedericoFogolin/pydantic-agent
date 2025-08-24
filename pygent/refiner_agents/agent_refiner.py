from __future__ import annotations

import os
from dataclasses import dataclass

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from supabase import Client

from ..prompts import prompt_refiner
from ..utils import (
    get_page_content_helper,
    list_documentation_pages_helper,
    retrieve_relevant_documentation_helper,
)

load_dotenv()
logfire.configure()

primary_llm_model = os.getenv("PRIMARY_MODEL", "gpt-4o")


@dataclass
class AgentRefinerDeps:
    supabase: Client
    embedding_client: AsyncOpenAI
    refinement_request: str


agent_refiner = Agent(
    primary_llm_model,
    system_prompt=prompt_refiner,
    deps_type=AgentRefinerDeps,
    retries=2,
)


@agent_refiner.system_prompt
def add_user_refinment_request(ctx: RunContext[AgentRefinerDeps]) -> str:
    return f"""User refinement request: {ctx.deps.refinement_request}"""


@agent_refiner.tool
async def retrieve_relevant_documentation(
    ctx: RunContext[AgentRefinerDeps], query: str
) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.
    Make sure your searches always focus on implementing the agent itself.

    Args:
        query: Your query to retrieve relevant documentation for implementing agents

    Returns:
        A formatted string containing the top 4 most relevant documentation chunks
    """
    return await retrieve_relevant_documentation_helper(
        ctx.deps.supabase, ctx.deps.embedding_client, query
    )


@agent_refiner.tool
async def list_documentation_pages(ctx: RunContext[AgentRefinerDeps]) -> list[str]:
    """
    Retrieve a list of all available Pydantic AI documentation pages.
    This will give you all pages available, but focus on the ones related to configuring agents and their dependencies.

    Returns:
        List[str]: List of unique URLs for all documentation pages
    """
    return await list_documentation_pages_helper(ctx.deps.supabase)


@agent_refiner.tool
async def get_page_content(ctx: RunContext[AgentRefinerDeps], url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.
    Only use this tool to get pages related to setting up agents with Pydantic AI.

    Args:
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    return await get_page_content_helper(ctx.deps.supabase, url)
