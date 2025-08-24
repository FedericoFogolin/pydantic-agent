from dataclasses import dataclass
from typing import Annotated


@dataclass
class GraphState:
    latest_user_message: str
    latest_model_message: str
    expert_conversation: Annotated[list[bytes], lambda x, y: x + y]
    triage_conversation: Annotated[list[bytes], lambda x, y: x + y]
    scope_conversation: Annotated[list[bytes], lambda x, y: x + y]

    user_intent: str
    scope: str

    refined_prompt: str
    refined_tool: str
    refined_agent: str
