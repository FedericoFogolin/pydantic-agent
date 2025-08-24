from __future__ import annotations
from dataclasses import dataclass
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_graph import BaseNode, GraphRunContext

from pygent.graph.state import GraphState
from pygent.agents.expert import pydantic_ai_expert, PydanticAIDeps
from pygent.graph.nodes.user_input import GetUserMessageNode


@dataclass
class ExpertNode(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> GetUserMessageNode:
        deps = PydanticAIDeps(
            user_intent=ctx.state.user_intent,
            reasoner_output=ctx.state.scope,
        )

        message_history: list[ModelMessage] = []
        for message_row in ctx.state.expert_conversation:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        result = await pydantic_ai_expert.run(
            ctx.state.latest_user_message,
            deps=deps,
            message_history=message_history,
        )
        ctx.state.expert_conversation = [result.new_messages_json()]
        return GetUserMessageNode(result.output)
# Code related to the Expert node
