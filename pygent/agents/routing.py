from pydantic_ai import Agent

from pygent.core.config import PRIMARY_LLM_MODEL, SMALL_LLM_MODEL

router_agent = Agent(
    PRIMARY_LLM_MODEL,
    system_prompt="""Your job is to route the user message either to the end of the conversation or to continue coding the AI agent.""",
)

refine_router_agent = Agent(
    SMALL_LLM_MODEL,
    instructions="""Your job is to decide which of the following categories the user's request falls into:
        1. `refine_prompt`: for request about refining the prompt for the agent.
        2. `refine_agent`: for request about refining the agent definition.

    Respond only with the category name.""",
)
