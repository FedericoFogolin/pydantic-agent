from pydantic_graph import Graph

from .state import GraphState
from .nodes import (
    TriageNode,
    DefineScopeNode,
    RefineScopeNode,
    ExpertNode,
    GetUserMessageNode,
    RefineRouterNode,
    RefineAgentNode,
    RefinePromptNode,
    FinishNode,
)

graph = Graph(
    nodes=[
        TriageNode,
        DefineScopeNode,
        RefineScopeNode,
        ExpertNode,
        GetUserMessageNode,
        RefineRouterNode,
        RefineAgentNode,
        RefinePromptNode,
        FinishNode,
    ],
    name="pygent",
    state_type=GraphState,
)
