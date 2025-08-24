import os
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_ai import Agent

load_dotenv()

reasoner_llm_model = os.getenv("REASONER_MODEL", "o3-mini")
primary_llm_model = os.getenv("PRIMARY_MODEL", "gpt-4o")


reasoner_agent = Agent(
    reasoner_llm_model,
    system_prompt="""You are an expert at coding AI agents with Pydantci AI and defining the scope for doing so.""",
)

router_agent = Agent(
    primary_llm_model,
    system_prompt="""Your job is to route the user message either to the end of the conversation or to continue coding the AI agent.""",
)

end_conversation_agent = Agent(
    primary_llm_model,
    system_prompt="""Your job is to end a conversation for creating an AI agent by giving instructions for how to execute the agent and they saying a nice goodbye to the user.""",
)


class TriageResult(BaseModel):
    """
    Represents the classified intent of a user's request.
    """

    intent: Literal["Development", "Q&A", "Chat"] = Field(
        description="The classified intent. Chat if unclear.",
    )
    reasoning: str = Field(
        ..., description="A brief explanation for the classification choice."
    )
    response_to_user: Optional[str] = Field(
        default=None,
        description="If the intent is unclear, this field contains a cordial response to the user, reminding them that the agent's purpose is to help with PydanticAI development.",
    )


triage_agent = Agent[None, TriageResult](
    primary_llm_model,
    output_type=TriageResult,
    system_prompt="""Your job is to analyze the user's request and classify its intent into one of two categories:
        1. Development: for request about creating or modifying code, agents or software.
        2. Q&A: for requests seeking information or explanations or brainstorming.
        3. Chat: if the request is conversational or unclear.

        If the intent is unclear and the request conversational ('hello', 'how are you?'), generate response_to_user conversationally reminding the user your purpose:
        help with Pydantic AI development.""",
)
