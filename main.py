import asyncio

import typer
from dotenv import load_dotenv
import logfire
from pydantic_graph import End

from nodes import DefineScopeNode, GetUserMessageNode, CoderNode, GraphState, graph
from utils import setup_logging

load_dotenv()
logfire.configure(scrubbing=False)
logfire.instrument_pydantic_ai()


def main():
    setup_logging()

    initial_message = typer.prompt("Enter the initial message")
    state = GraphState(
        latest_user_message=initial_message,
        messages=[],
        scope=None,
    )

    async def run_graph():
        node = DefineScopeNode()
        async with graph.iter(node, state=state) as run:
            while True:
                node = await run.next(node)
                if isinstance(node, End):
                    print("END: ", node.data)
                    break
                elif isinstance(node, GetUserMessageNode):
                    print("\n\n")
                    print(node.coder_output)
                    print("\n\n")
                    user_input = typer.prompt("Enter your message")
                    state.latest_user_message = user_input
                    continue
            print(run.result)

    asyncio.run(run_graph())


if __name__ == "__main__":
    main()
