from pydantic_ai import Agent
from pygent.core.config import PRIMARY_LLM_MODEL

end_conversation_agent = Agent(
    PRIMARY_LLM_MODEL,
    system_prompt='''Your job is to end a conversation for creating an AI agent by giving instructions for how to execute the agent and they saying a nice goodbye to the user.''',
)
