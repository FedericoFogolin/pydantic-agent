from pathlib import Path

import logfire
from pydantic_graph import End
from pydantic_graph.persistence.file import FileStatePersistence

from nodes import CoderNode, DefineScopeNode, GetUserMessageNode, GraphState, graph

logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()


async def run_graph(run_id: str, user_input: str):
    persistence = FileStatePersistence(Path(f"workbench/{run_id}.json"))
    persistence.set_graph_types(graph)
    if snapshot := await persistence.load_next():
        state = snapshot.state
        assert user_input != ""
        node = GetUserMessageNode(user_message=user_input)
    else:
        state = GraphState(user_input, [])
        node = DefineScopeNode()

    async with graph.iter(node, state=state, persistence=persistence) as run:
        while True:
            node = await run.next()

            if isinstance(node, End):
                history = await persistence.load_all()
                print([e.node for e in history])
                return node.data

            elif isinstance(node, GetUserMessageNode):
                print(node.code_output)
                return node.code_output
