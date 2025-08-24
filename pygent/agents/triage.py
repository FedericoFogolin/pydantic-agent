from typing import Literal, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent

from pygent.core.config import PRIMARY_LLM_MODEL
from pygent.prompts.triage import triage


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
    system_prompt=triage,
)
