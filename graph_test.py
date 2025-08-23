from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Optional

from pydantic_graph import BaseNode, End, Graph, GraphRunContext
from pydantic_graph.persistence.file import FileStatePersistence


@dataclass
class GraphState:
    latest_user_message: str
    foo_: int
    scope: Optional[str] = None


@dataclass
class DefineScopeNode(BaseNode[GraphState, None]):
    async def run(self, ctx: GraphRunContext[GraphState]) -> CoderNode:
        print("1")
        ctx.state.foo_ += 1
        return CoderNode(ctx.state.foo_ + 1)


@dataclass
class CoderNode(BaseNode[GraphState, None]):
    foo: int

    async def run(self, ctx: GraphRunContext[GraphState]) -> GetUserMessageNode:
        print("2")
        ctx.state.foo_ += 1
        return GetUserMessageNode(self.foo + 1)


@dataclass
class GetUserMessageNode(BaseNode[GraphState, None]):
    foo: int

    async def run(
        self, ctx: GraphRunContext[GraphState]
    ) -> FinishConversationNode | CoderNode:
        print("3")
        ctx.state.foo_ += 1
        return FinishConversationNode(self.foo + 1)


@dataclass
class FinishConversationNode(BaseNode[GraphState, None, int]):
    foo: int

    async def run(self, ctx: GraphRunContext[GraphState]) -> End[int]:
        print("4")
        ctx.state.foo_ += 1
        return End(self.foo + 1)


graph = Graph(
    nodes=[DefineScopeNode, CoderNode, GetUserMessageNode, FinishConversationNode]
)


async def run_node(run_id: str) -> bool:
    persistence = FileStatePersistence(Path(f"workbench/{run_id}.json"))
    async with graph.iter_from_persistence(persistence) as run:
        node = await run.next()
    print("Node: ", node)
    return isinstance(node, End) | isinstance(node, GetUserMessageNode)


async def main_persistence():
    run_id = "run_124"
    persistence = FileStatePersistence(Path(f"workbench/{run_id}.json"))
    state = GraphState("hello", 1)
    await graph.initialize(DefineScopeNode(), state=state, persistence=persistence)

    done = False
    while not done:
        done = await run_node(run_id)


async def main():
    state = GraphState("hello", 1)
    graph = Graph(
        nodes=[DefineScopeNode, CoderNode, GetUserMessageNode, FinishConversationNode]
    )

    result = await graph.run(DefineScopeNode(), state=state)
    print(result.output)


async def iterate_graph():
    state = GraphState("hello", 1)
    graph = Graph(
        nodes=[DefineScopeNode, CoderNode, GetUserMessageNode, FinishConversationNode]
    )

    async with graph.iter(DefineScopeNode(), state=state) as run:
        async for node in run:
            print("Node:", node)

    print("final:", run.result)


async def manual_iter():
    state = GraphState("hello", 1)
    graph = Graph(
        nodes=[DefineScopeNode, CoderNode, GetUserMessageNode, FinishConversationNode]
    )

    async with graph.iter(DefineScopeNode(), state=state) as run:
        node = run.next_node

        while not isinstance(node, End):
            print("Node:", node)
            if state.foo_ == 3:
                break

            node = await run.next(node)

        print(run.result)


asyncio.run(main_persistence())
