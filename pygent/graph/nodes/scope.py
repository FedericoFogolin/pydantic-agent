from __future__ import annotations
import os
from dataclasses import dataclass
from pydantic_graph import BaseNode, GraphRunContext

from pygent.graph.state import GraphState
from pygent.agents.reasoner import reasoner_agent
from pygent.tools.documentation import list_documentation_pages_helper
from pygent.graph.nodes.expert import ExpertNode


@dataclass
class DefineScopeNode(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> ExpertNode:
        documentation_pages = await list_documentation_pages_helper()
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


# Code related to the Scope node
