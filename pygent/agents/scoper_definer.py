from pydantic import BaseModel, Field
from pydantic_ai import Agent

from pygent.core.config import PRIMARY_LLM_MODEL, REASONER_LLM_MODEL

scope_definer_agent = Agent(
    REASONER_LLM_MODEL,
    system_prompt="You are an expert at coding AI agents with Pydantic AI and defining the scope for doing so.",
)


class ScopeSummary(BaseModel):
    scope_summary: str = Field(
        ...,
        description="A comprehensive summary of the scope received, for the user to review.",
    )


summarize_scope_agent = Agent(
    PRIMARY_LLM_MODEL,
    instructions="""Your goal is to priovide a summary of the scope of the project you will receive.
        Ensure to don't miss any important information as the summary it's intended for the scope review.""",
    output_type=ScopeSummary,
)


class ScopeRefinement(BaseModel):
    scope_summary: str = Field(
        ...,
        description="A summary of the scope received, for the user to review.",
    )
    user_message: str = Field(
        ...,
        description="The user message that the user sent as feedback.",
    )
    refinement_feedback: str = Field(
        ...,
        description="How the next agent should improve the original scope based on the user feedback.",
    )
    approved: bool = Field(
        default=False, description="Whether the user approved the scope."
    )


refine_scope_agent = Agent(
    PRIMARY_LLM_MODEL,
    system_prompt="Your goal is to understand if the user has approved the scope and if not, provide feedback on how to improve it.",
    output_type=ScopeRefinement,
)
