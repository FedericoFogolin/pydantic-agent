from __future__ import annotations
from dataclasses import dataclass
from pydantic_graph import BaseNode, GraphRunContext

from pygent.graph.state import GraphState
from pygent.agents.routing import router_agent
from pygent.graph.nodes.expert import ExpertNode
from pygent.graph.nodes.refine import RefineRouter
from pygent.graph.nodes.finish import FinishConversationNode


@dataclass
class GetUserMessageNode(BaseNode[GraphState, None]):
    code_output: str | None = None
    user_message: str | None = None

    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> FinishConversationNode | ExpertNode | RefineRouter:
        prompt = f"""
        The user has sent a message: 
        
        {self.user_message}

        If the user wants to end the conversation, respond with just the text "finish_conversation".
        If the user wants to continue coding the AI agent, respond with just the text "coder_agent".
        If the user asks specifically to "refine" the agent, respond with just the text "refine".
        """
        if self.user_message is not None:
            ctx.state.latest_user_message = self.user_message

        result = await router_agent.run(prompt)
        next_node = result.output

        if next_node == "finish_conversation":
            return FinishConversationNode()
        if next_node == "refine":
            return RefineRouter()
        else:
            return ExpertNode()
