from pygent.tools import mermaid_code
from pygent.graph import graph
from pygent.graph.nodes import Triage


def main():
    mermaid_code(graph, start_node=Triage)


if __name__ == "__main__":
    main()
