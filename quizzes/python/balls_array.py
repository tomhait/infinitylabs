def get_sorted_balls(arr: list):
    """
    O(n log n) time complexity
    O(n) space complexity
    """
    num_dict = {"green": 0, "yellow": 1, "red": 2}
    arr.sort(key=lambda x: num_dict[x])
    return arr

def sort_balls(balls):
    """
    O(n) time complexity
    O(1) space complexity
    """
    for i, ball in enumerate(balls):
        if ball == "green":
            balls.pop(i)
            balls.insert(0,ball)
        elif ball == "red":
            balls.pop(i)
            balls.insert(len(balls)-1,ball)
    return balls


arr = ['red', 'yellow', 'green', 'yellow', 'red', 'green']
print(f"Sorted: {sort_balls(arr)}")
arr = ['red', 'yellow', 'green', 'yellow', 'red', 'green']
print(f"Sorted: {get_sorted_balls(arr)}")