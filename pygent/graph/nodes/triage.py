from __future__ import annotations

from dataclasses import dataclass

import logfire
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_graph import BaseNode, GraphRunContext

from pygent.agents.triage import triage_agent
from pygent.graph.nodes.expert import ExpertNode
from pygent.graph.nodes.scope import DefineScope
from pygent.graph.state import GraphState


@dataclass
class TriageNode(BaseNode[GraphState, None]):
    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> DefineScope | ExpertNode | TriageNode:
        message_history: list[ModelMessage] = []
        for message_row in ctx.state.triage_conversation:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        result = await triage_agent.run(
            ctx.state.latest_user_message, message_history=message_history
        )
        logfire.info(f"Triage result: {result.output.intent}")
        ctx.state.triage_conversation = [result.new_messages_json()]

        if result.output.intent == "Q&A":
            ctx.state.user_intent = result.output.intent
            return ExpertNode()
        elif result.output.intent == "Development":
            ctx.state.user_intent = result.output.intent
            return DefineScope()
        else:
            ctx.state.user_intent = result.output.intent
            assert result.output.response_to_user is not None
            ctx.state.latest_model_message = result.output.response_to_user
            return TriageNode()


# Code related to the Triage node
