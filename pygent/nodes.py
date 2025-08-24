from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from supabase import Client

from .agents import (
    end_conversation_agent,
    reasoner_agent,
    refine_router_agent,
    router_agent,
    triage_agent,
)
from .py_ai_expert import (
    PydanticAIDeps,
    list_documentation_pages_helper,
    pydantic_ai_expert,
)
from .refiner_agents import AgentRefinerDeps, agent_refiner, prompt_refiner

load_dotenv()

logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()

openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
supabase: Client = Client(
    os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVICE_KEY", "")
)


@dataclass
class GraphState:
    latest_user_message: str
    latest_model_message: str
    expert_conversation: Annotated[list[bytes], lambda x, y: x + y]
    triage_conversation: Annotated[list[bytes], lambda x, y: x + y]

    user_intent: str
    scope: str

    refined_prompt: str
    refined_tool: str
    refined_agent: str


@dataclass
class Triage(BaseNode[GraphState, None]):
    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> DefineScope | ExpertNode | Triage:
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
            return Triage()


@dataclass
class DefineScope(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> ExpertNode:
        documentation_pages = await list_documentation_pages_helper(supabase)
        documentation_pages_str = "\n".join(documentation_pages)
        prompt = f"""
        User AI Agent Request: {ctx.state.latest_user_message}
        
        Create detailed scope document for the AI agent including:
        - Architecture diagram
        - Core components
        - External dependencies
        - Testing strategy

        Also based on these documentation pages available:

        {documentation_pages_str}

        Include a list of documentation pages that are relevant to creating this agent for the user in the scope document.
        """

        result = await reasoner_agent.run(prompt)
        scope = result.output
        ctx.state.scope = scope

        scope_path = os.path.join("workbench", "scope.md")
        os.makedirs("workbench", exist_ok=True)
        with open(scope_path, "w", encoding="utf-8") as f:
            f.write(scope)

        return ExpertNode()


@dataclass
class ExpertNode(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> GetUserMessageNode:
        deps = PydanticAIDeps(
            supabase=supabase,
            embedding_client=openai_client,
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


@dataclass
class RefineRouter(BaseNode[GraphState, None]):
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
        result = await prompt_refiner.run(prompt, message_history=message_history)
        ctx.state.refined_prompt = result.output
        return ExpertNode()


@dataclass
class RefineAgent(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> ExpertNode:
        deps = AgentRefinerDeps(
            supabase=supabase,
            embedding_client=openai_client,
            refinement_request=ctx.state.latest_user_message,
        )
        message_history: list[ModelMessage] = []
        for message_row in ctx.state.expert_conversation:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        prompt = "Based on the current conversation, refine the agent definition."
        result = await agent_refiner.run(
            prompt, message_history=message_history, deps=deps
        )
        ctx.state.refined_agent = result.output
        return ExpertNode()


@dataclass
class FinishConversationNode(BaseNode[GraphState, None, str]):
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


graph = Graph(
    nodes=[
        Triage,
        DefineScope,
        ExpertNode,
        GetUserMessageNode,
        FinishConversationNode,
        RefineRouter,
        RefinePrompt,
        RefineAgent,
    ],
    name="pyagent",
    state_type=GraphState,
)
