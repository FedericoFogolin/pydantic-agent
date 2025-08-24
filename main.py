from utils.utils import mermaid_code
from pygent.nodes import graph, Triage


def main():
    mermaid_code(graph, start_node=Triage)


if __name__ == "__main__":
    main()
