from __future__ import annotations

from dataclasses import dataclass

import logfire
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from supabase import Client

from pygent.core.clients import openai_client, supabase_client
from pygent.core.config import PRIMARY_LLM_MODEL
from pygent.tools.documentation import (
    get_page_content_helper,
    list_documentation_pages_helper,
    retrieve_relevant_documentation_helper,
)

from .agent_refiner_prompt import agent_refiner_prompt


logfire.configure()


@dataclass
class AgentRefinerDeps:
    refinement_request: str
    supabase: Client = supabase_client
    embedding_client: AsyncOpenAI = openai_client


agent_refiner_agent = Agent(
    PRIMARY_LLM_MODEL,
    system_prompt=agent_refiner_prompt,
    deps_type=AgentRefinerDeps,
    retries=2,
)


@agent_refiner_agent.system_prompt
def add_user_refinment_request(ctx: RunContext[AgentRefinerDeps]) -> str:
    return f"""User refinement request: {ctx.deps.refinement_request}"""


@agent_refiner_agent.tool
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
        query, ctx.deps.supabase, ctx.deps.embedding_client
    )


@agent_refiner_agent.tool
async def list_documentation_pages(ctx: RunContext[AgentRefinerDeps]) -> list[str]:
    """
    Retrieve a list of all available Pydantic AI documentation pages.
    This will give you all pages available, but focus on the ones related to configuring agents and their dependencies.

    Returns:
        List[str]: List of unique URLs for all documentation pages
    """
    return await list_documentation_pages_helper(ctx.deps.supabase)


@agent_refiner_agent.tool
async def get_page_content(ctx: RunContext[AgentRefinerDeps], url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.
    Only use this tool to get pages related to setting up agents with Pydantic AI.

    Args:
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    return await get_page_content_helper(url, ctx.deps.supabase)
