from dataclasses import dataclass
from typing import Optional

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

from .expert_prompt import coder_expert_prompt, docs_expert_prompt

logfire.configure()


@dataclass
class PydanticAIDeps:
    user_intent: str
    supabase: Client = supabase_client
    embedding_client: AsyncOpenAI = openai_client
    reasoner_output: Optional[str] = None


expert_agent = Agent(PRIMARY_LLM_MODEL, deps_type=PydanticAIDeps, retries=2)


@expert_agent.system_prompt
def add_base_prompt(ctx: RunContext[PydanticAIDeps]) -> str:
    coder_prompt = coder_expert_prompt
    expert_prompt = docs_expert_prompt
    return coder_prompt if ctx.deps.user_intent == "Development" else expert_prompt


@expert_agent.system_prompt
def add_reasoner_output(ctx: RunContext[PydanticAIDeps]) -> str:
    return (
        f"""
    \n\nAdditional thoughts/instructions from the reasoner LLM.
    This scope includes documentation pages for you to search as well:
    {ctx.deps.reasoner_output}
    """
        if ctx.deps.user_intent == "Development"
        else ""
    )


@expert_agent.tool
async def retrieve_relevant_documentation(
    ctx: RunContext[PydanticAIDeps],
    user_query: str,
) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.

    Args:
        user_query: The user's question or query

    Returns:
        A formatted string containing the top 4 most relevant documentation chunks
    """
    return await retrieve_relevant_documentation_helper(
        user_query, ctx.deps.supabase, ctx.deps.embedding_client
    )


@expert_agent.tool
async def list_documentation_pages(ctx: RunContext[PydanticAIDeps]) -> list[str]:
    """
    Retrieve a list of all available Pydantic AI documentation pages.

    Returns:
        List[str]: List of unique URLs for all documentation pages
    """
    return await list_documentation_pages_helper(ctx.deps.supabase)


@expert_agent.tool
async def get_page_content(ctx: RunContext[PydanticAIDeps], url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.

    Args:
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    return await get_page_content_helper(url, ctx.deps.supabase)
