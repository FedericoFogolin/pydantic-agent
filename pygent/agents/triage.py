from typing import Literal, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from pygent.core.config import PRIMARY_LLM_MODEL


class TriageResult(BaseModel):
    """
    Represents the classified intent of a user's request.
    """

    intent: Literal["Development", "Q&A", "Chat"] = Field(
        description="The classified intent. Chat if unclear.",
    )
    user_request: str = Field(..., description="The request of the user.")
    reasoning: str = Field(
        ..., description="A brief explanation for the classification choice."
    )
    response_to_user: Optional[str] = Field(
        default=None,
        description="If the intent is unclear, this field contains a cordial response to the user, reminding them that the agent's purpose is to help with PydanticAI development.",
    )


triage_agent = Agent[None, TriageResult](
    PRIMARY_LLM_MODEL,
    output_type=TriageResult,
    system_prompt="""Your goal is to identify the user request intent among the following options:
    1. 'Q&A': when the user is requesting specific information or brainstorming ideas.
    2. 'Development': when the user is requesting to develop or build or add features.
    3. 'Chat': whene the request is conversational and no specific intent is identified.
    """,
)
