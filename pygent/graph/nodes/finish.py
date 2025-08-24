from __future__ import annotations
from dataclasses import dataclass
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_graph import BaseNode, End, GraphRunContext

from pygent.graph.state import GraphState
from pygent.agents.conversation import end_conversation_agent


@dataclass
class FinishNode(BaseNode[GraphState, None, str]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> End[str]:
        message_history: list[ModelMessage] = []
        for message_row in ctx.state.expert_conversation:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        result = await end_conversation_agent.run(
            ctx.state.latest_user_message,
            message_history=message_history,
        )
        ctx.state.expert_conversation = [result.new_messages_json()]
        return End(result.output)
