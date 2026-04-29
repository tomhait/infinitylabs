def hanoi(n, source, to, aux):
    if n>0:
        hanoi(n-1, source, aux, to)
        print(f"Disk {n} moved from {source} to {to}")
        hanoi(n-1, aux, to, source)


hanoi(3, 'A', 'C', 'B')