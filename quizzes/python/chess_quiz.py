import sys

def mark_rook_path(table, rook_pos, blocking_king_pos):
    r, c = rook_pos
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    for dr, dc in directions:
        curr_r, curr_c = r + dr, c + dc
        while 0 <= curr_r < 8 and 0 <= curr_c < 8:
            if (curr_r, curr_c) == blocking_king_pos:
                break

            table[curr_r][curr_c] = 1
            curr_r += dr
            curr_c += dc


data = sys.stdin.read().split()
rook1 = data[0]
rook2 = data[1]
king1 = data[2]
king2 = data[3]
rows, cols = 8, 8
table = [[0 for x in range(rows)] for y in range(cols)]

locator = {
    'a': 0,
    'b': 1,
    'c': 2,
    'd': 3,
    'e': 4,
    'f': 5,
    'g': 6,
    'h': 7
}
rook1_loc = int(rook1[1])-1, locator[rook1[0]]
rook2_loc = int(rook2[1])-1, locator[rook2[0]]
king1_loc = int(king1[1])-1, locator[king1[0]]
king2_loc = int(king2[1])-1, locator[king2[0]]


king1_options = [(king1_loc[0]+1,king1_loc[1]),
                   (king1_loc[0]-1,king1_loc[1]),
                   (king1_loc[0]+1,king1_loc[1]+1),
                   (king1_loc[0]-1,king1_loc[1]+1),
                   (king1_loc[0]+1,king1_loc[1]-1),
                   (king1_loc[0]-1,king1_loc[1]-1),
                   (king1_loc[0],king1_loc[1]+1),
                   (king1_loc[0],king1_loc[1]-1)]


mark_rook_path(table, rook1_loc, king1_loc)
mark_rook_path(table, rook2_loc, king1_loc)

for row, col in king1_options:
  if row < 0 or row > 7 or col > 7 or col < 0:
    continue
  table[row][col] = 1

king2_options = [(king2_loc[0]+1,king2_loc[1]),
                   (king2_loc[0]-1,king2_loc[1]),
                   (king2_loc[0]+1,king2_loc[1]+1),
                   (king2_loc[0]-1,king2_loc[1]+1),
                   (king2_loc[0]+1,king2_loc[1]-1),
                   (king2_loc[0]-1,king2_loc[1]-1),
                   (king2_loc[0],king2_loc[1]+1),
                   (king2_loc[0],king2_loc[1]-1),
                   (king2_loc[0],king2_loc[1])]

flag = 1
for row, col in king2_options:
  if row < 0 or row > 7 or col > 7 or col < 0:
    continue
  elif table[row][col] == 0:
    print('OTHER')
    flag = 0
if flag:
    print('CHECKMATE')
for row in table:
  print(row)