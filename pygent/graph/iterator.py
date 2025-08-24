from pathlib import Path

import logfire
from pydantic_graph import End
from pydantic_graph.persistence.file import FileStatePersistence

from pygent.graph.nodes import TriageNode, GetUserMessageNode

from .graph import graph
from .state import GraphState


logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()


async def run_graph(run_id: str, user_input: str):
    persistence = FileStatePersistence(Path(f"workbench/{run_id}.json"))
    persistence.set_graph_types(graph)

    if snapshot := await persistence.load_next():
        state = snapshot.state
        assert user_input != ""
        state.latest_user_message = user_input
        if state.user_intent == "Development":
            node = GetUserMessageNode(user_message=user_input)
        elif state.user_intent == "Q&A":
            node = TriageNode()
        else:
            node = TriageNode()
    else:
        state = GraphState(
            latest_user_message=user_input,
            latest_model_message="",
            triage_conversation=[],
            expert_conversation=[],
            user_intent="",
            scope="",
            refined_prompt="",
            refined_tool="",
            refined_agent="",
        )
        node = TriageNode()

    async with graph.iter(node, state=state, persistence=persistence) as run:
        while True:
            node = await run.next()
            print(node)

            if isinstance(node, End):
                history = await persistence.load_all()
                print([e.node for e in history])
                return node.data

            elif isinstance(node, GetUserMessageNode):
                print(node.code_output)
                return node.code_output

            elif isinstance(node, TriageNode):
                print(state.user_intent)
                return state.latest_model_message
