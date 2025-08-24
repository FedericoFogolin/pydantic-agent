from utils.utils import mermaid_code
from pygent.graph import graph
from pygent.graph.nodes import TriageNode


def main():
    mermaid_code(graph, start_node=TriageNode)


if __name__ == "__main__":
    main()
