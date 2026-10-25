"""
draw_graph.py — save a picture of the graph:   python draw_graph.py
Then open graph.mmd, copy everything, and paste it at https://mermaid.live
"""

from graph import graph

with open("graph.mmd", "w") as file:
    file.write(graph.get_graph().draw_mermaid())

print("Saved graph.mmd. Paste it at https://mermaid.live to see the picture.")
