from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Annotated, Optional

import logfire
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.messages import ModelMessage, ModelMessagesTypeAdapter
from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from supabase import Client

from .agents import end_conversation_agent, reasoner_agent, router_agent
from .py_ai_expert import (
    PydanticAIDeps,
    list_documentation_pages_helper,
    pydantic_ai_coder,
)

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
    messages: Annotated[list[bytes], lambda x, y: x + y]
    scope: Optional[str] = None


@dataclass
class DefineScopeNode(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> CoderNode:
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

        return CoderNode()


@dataclass
class CoderNode(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> GetUserMessageNode:
        deps = PydanticAIDeps(
            supabase=supabase,
            embedding_client=openai_client,
            reasoner_output=ctx.state.scope,
        )

        message_history: list[ModelMessage] = []
        for message_row in ctx.state.messages:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        result = await pydantic_ai_coder.run(
            ctx.state.latest_user_message,
            deps=deps,
            message_history=message_history,
        )
        ctx.state.messages = [result.new_messages_json()]
        return GetUserMessageNode(result.output)


@dataclass
class GetUserMessageNode(BaseNode[GraphState, None]):
    code_output: str | None = None
    user_message: str | None = None

    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> FinishConversationNode | CoderNode:
        prompt = f"""
        The user has sent a message: 
        
        {self.user_message}

        If the user wants to end the conversation, respond with just the text "finish_conversation".
        If the user wants to continue coding the AI agent, respond with just the text "coder_agent".
        """
        if self.user_message is not None:
            ctx.state.latest_user_message = self.user_message

        result = await router_agent.run(prompt)
        next_node = result.output

        if next_node == "finish_conversation":
            return FinishConversationNode()
        else:
            return CoderNode()


@dataclass
class FinishConversationNode(BaseNode[GraphState, None, str]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> End[str]:
        message_history: list[ModelMessage] = []
        for message_row in ctx.state.messages:
            message_history.extend(ModelMessagesTypeAdapter.validate_json(message_row))

        result = await end_conversation_agent.run(
            ctx.state.latest_user_message,
            message_history=message_history,
        )
        ctx.state.messages = [result.new_messages_json()]
        return End(result.output)


graph = Graph(
    nodes=[
        DefineScopeNode,
        CoderNode,
        GetUserMessageNode,
        FinishConversationNode,
    ],
    name="pyagent",
    state_type=GraphState,
)
