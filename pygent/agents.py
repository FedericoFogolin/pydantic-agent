import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic import BaseModel, Field

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


class ConciergeOutput(BaseModel):
    """The output of the concierge agent."""

    intent: str = Field(
        description="The user's intent. Must be one of: 'chat', 'build_agent', 'explain_concept'."
    )
    response: str = Field(description="The chat response to the user.")


concierge_agent = Agent[None, ConciergeOutput](
    primary_llm_model,
    output_type=ConciergeOutput,
)
