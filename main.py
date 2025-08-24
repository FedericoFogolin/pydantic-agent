from utils.utils import mermaid_code
from pygent.graph import graph, nodes


def main():
    mermaid_code(graph, start_node=nodes.TriageNode)


if __name__ == "__main__":
    main()
