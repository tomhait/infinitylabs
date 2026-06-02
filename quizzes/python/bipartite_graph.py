from collections import deque

def is_bipartite(graph: dict):
    color = {}
    for node in graph:
        if node not in color:
            queue = deque([node])
            color[node] = 0

            while queue:
                current = queue.popleft()
                for neigh in graph[current]:
                    if neigh not in color:
                        color[neigh] = 1- color[current]
                        queue.append(neigh)
                    elif color[neigh] == color[current]:
                        return False
    return True

graph_a = {0: [1, 3], 1: [0, 2], 2: [1, 3], 3: [0, 2]}
print(f"Is Graph A Bipartite? {is_bipartite(graph_a)}")  # True

graph_b = {0: [1, 2], 1: [0, 2], 2: [0, 1]}
print(f"Is Graph B Bipartite? {is_bipartite(graph_b)}") # False