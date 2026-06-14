import sys
queens = set()
chess_board = None
first_line_flag = True
for line in sys.stdin:
    clean_line = line.strip().split()
    if first_line_flag:
        chess_board = int(clean_line[0])
        num_queens = int(clean_line[1])
        first_line_flag = False
        continue
    queens.add((int(clean_line[0]), int(clean_line[1])))

def check_queens(qu, queens, chess_board, direction):
    while True:
        if not (0 <= qu[0] <= chess_board and 0 <= qu[1] <= chess_board):
            return 0, None
        if qu in queens:
            return 1, qu
        qu = (qu[0] + direction[0], qu[1] + direction[1])

visited = {qu:[] for qu in queens}
directions = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
t = [0]*9

for qu in queens:
    for direction in directions:
        if direction in visited[qu]:
          continue
        out, hit_qu = check_queens((qu[0] + direction[0], qu[1] + direction[1]), queens, chess_board, direction)
        if out:
            visited[qu].append(direction)
            visited[hit_qu].append(tuple(x * -1 for x in direction))

for qu in queens:
    t[len(visited[qu])] += 1

print(*t)