def numIslands(grid):
    if not grid:
        return 0

    rows = len(grid)
    cols = len(grid[0])
    island_count = 0
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                  (-1, -1), (1, 1), (-1, 1), (1, -1)]

    def sink(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or grid[r][c] == '0':
            return
        grid[r][c] = '0'

        for dr, dc in directions:
            sink(r + dr, c + dc)

    for r in range(rows):
        for c in range(cols):
            if (r == 0 or r == rows - 1 or c == 0 or c == cols - 1) and grid[r][c] == '1':
                sink(r, c)

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                island_count += 1
                sink(r, c)

    return island_count



example_grid = [
    ["1", "1", "1", "0", "0", "0"],
    ["0", "1", "0", "0", "1", "0"],
    ["0", "1", "0", "1", "1", "0"],
    ["0", "0", "0", "0", "0", "0"]
]

print(f"Number of islands: {numIslands(example_grid)}") # 1

example_grid = [
    ["1", "1", "1", "0", "0", "0"],
    ["0", "0", "0", "0", "1", "0"],
    ["0", "1", "0", "1", "1", "0"],
    ["0", "0", "0", "0", "0", "0"]
]

print(f"Number of islands: {numIslands(example_grid)}") # 2

example_grid = [
    ["1", "1", "1", "0", "0", "0"],
    ["0", "1", "0", "0", "1", "0"],
    ["0", "1", "0", "1", "1", "0"],
    ["0", "0", "1", "0", "0", "0"]
]

print(f"Number of islands: {numIslands(example_grid)}") # 0
