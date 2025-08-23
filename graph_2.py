from pathlib import Path

import logfire
from pydantic_graph import End
from pydantic_graph.persistence.file import FileStatePersistence

from nodes_2 import (
    CoderNode,
    DefineScopeNode,
    GraphState,
    graph,
    EvaluateUserMessage,
)

logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()


async def run_graph(run_id: str, user_input: str):
    persistence = FileStatePersistence(Path(f"workbench/{run_id}.json"))
    persistence.set_graph_types(graph)
    if snapshot := await persistence.load_next():
        state = snapshot.state
        print("******************************")
        logfire.info(f"Loaded state: {state}")
        assert user_input != ""
        node = EvaluateUserMessage(user_message=user_input)
    else:
        print("EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
        state = GraphState(user_input, [])
        node = DefineScopeNode()

    result = await graph.run(node, state=state, persistence=persistence)
    return result.output
