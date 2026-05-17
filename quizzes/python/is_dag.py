from collections import deque


def is_dag(adj_mat: dict):
    inDeg = [0] * len(adj_mat)
    q = deque()
    visited = 0

    for v in adj_mat:
        for adj in adj_mat[v]:
            inDeg[adj] += 1

    for v in range(len(inDeg)):
        if inDeg[v] == 0:
            q.append(v)

    while q:
        u = q.popleft()
        visited += 1

        for v in adj_mat[u]:
            inDeg[v] -= 1
            if inDeg[v] == 0:
                q.append(v)

    return visited == len(adj_mat)

adj_mat = {
    0: [1],
    1: [2],
    2: [3],
    3: []
}

print(is_dag(adj_mat))

adj_mat = {
    0: [1],
    1: [2],
    2: [3],
    3: [0]
}

print(is_dag(adj_mat))