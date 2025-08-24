from utils.utils import mermaid_code
from pygent.nodes import graph, DefineScopeNode


def main():
    mermaid_code(graph, start_node=DefineScopeNode)


if __name__ == "__main__":
    main()
