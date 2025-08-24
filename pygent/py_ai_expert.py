from dataclasses import dataclass
from typing import Optional

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from supabase import Client

from .prompts import docs_expert, primary_coder
from .utils import (
    get_page_content_helper,
    list_documentation_pages_helper,
    retrieve_relevant_documentation_helper,
)

load_dotenv()
llm = "openai:gpt-4o"
logfire.configure()


@dataclass
class PydanticAIDeps:
    supabase: Client
    embedding_client: AsyncOpenAI
    user_intent: Optional[str] = None
    reasoner_output: Optional[str] = None


pydantic_ai_expert = Agent(llm, deps_type=PydanticAIDeps, retries=2)


@pydantic_ai_expert.system_prompt
def select_base_prompt(ctx: RunContext[PydanticAIDeps]) -> str:
    coder_prompt = primary_coder
    expert_prompt = docs_expert
    return coder_prompt if ctx.deps.user_intent == "Development" else expert_prompt


@pydantic_ai_expert.system_prompt
def add_reasoner_output(ctx: RunContext[PydanticAIDeps]) -> str:
    return f"""
    \n\nAdditional thoughts/instructions from the reasoner LLM.
    This scope includes documentation pages for you to search as well:
    {ctx.deps.reasoner_output}
    """


@pydantic_ai_expert.tool
async def retrieve_relevant_documentation(
    ctx: RunContext[PydanticAIDeps], user_query: str
) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.

    Args:
        user_query: The user's question or query

    Returns:
        A formatted string containing the top 4 most relevant documentation chunks
    """
    return await retrieve_relevant_documentation_helper(
        ctx.deps.supabase, ctx.deps.embedding_client, user_query
    )


@pydantic_ai_expert.tool
async def list_documentation_pages(ctx: RunContext[PydanticAIDeps]) -> list[str]:
    """
    Retrieve a list of all available Pydantic AI documentation pages.

    Returns:
        List[str]: List of unique URLs for all documentation pages
    """
    return await list_documentation_pages_helper(ctx.deps.supabase)


@pydantic_ai_expert.tool
async def get_page_content(ctx: RunContext[PydanticAIDeps], url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.

    Args:
        url: The URL of the page to retrieve

    Returns:
        str: The complete page content with all chunks combined in order
    """
    return await get_page_content_helper(ctx.deps.supabase, url)
