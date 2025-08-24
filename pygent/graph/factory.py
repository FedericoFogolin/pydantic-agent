from pydantic_graph import Graph

from pygent.graph.state import GraphState
from pygent.graph.nodes.triage import Triage
from pygent.graph.nodes.scope import DefineScope
from pygent.graph.nodes.expert import ExpertNode
from pygent.graph.nodes.user_input import GetUserMessageNode
from pygent.graph.nodes.finish import FinishConversationNode
from pygent.graph.nodes.refine import RefineRouter, RefinePrompt, RefineAgent

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
# Code related to the Graph factory
