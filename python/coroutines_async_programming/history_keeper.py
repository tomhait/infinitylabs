def history_keeper(n):
    history = []
    while True:
        received = yield history
        if len(history) == n:
            history.pop(0)
        history.append(received)

hk = history_keeper(3)
print(next(hk))
print(hk.send(1))
print(hk.send(2))
print(hk.send(3))
print(hk.send(4))
