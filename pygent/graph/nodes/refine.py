from __future__ import annotations
from dataclasses import dataclass
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_graph import BaseNode, GraphRunContext

from pygent.graph.state import GraphState
from pygent.agents.routing import refine_router_agent
from pygent.agents.refiners.prompt import prompt_refiner_agent
from pygent.agents.refiners.agent import agent_refiner_agent, AgentRefinerDeps
from pygent.graph.nodes.expert import ExpertNode


@dataclass
class RefineRouterNode(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> RefinePrompt | RefineAgent:
        result = await refine_router_agent.run(ctx.state.latest_user_message)
        if result.output == "refine_prompt":
            return RefinePrompt()
        if result.output == "refine_agent":
            return RefineAgent()
        else:
            raise ValueError(f"Invalid refine request: {result.output}")


@dataclass
class RefinePrompt(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> ExpertNode:
        message_history: list[ModelMessage] = []
        for message_row in ctx.state.expert_conversation:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        prompt = "Based on the current conversation, refine the prompt for the agent."
        result = await prompt_refiner_agent.run(prompt, message_history=message_history)
        ctx.state.refined_prompt = result.output
        return ExpertNode()


@dataclass
class RefineAgent(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> ExpertNode:
        deps = AgentRefinerDeps(
            refinement_request=ctx.state.latest_user_message,
        )
        message_history: list[ModelMessage] = []
        for message_row in ctx.state.expert_conversation:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        prompt = "Based on the current conversation, refine the agent definition."
        result = await agent_refiner_agent.run(
            prompt, message_history=message_history, deps=deps
        )
        ctx.state.refined_agent = result.output
        return ExpertNode()
