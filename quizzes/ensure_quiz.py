from functools import wraps

def ensure(var_type):
    def decorator(func):
        @wraps(func)
        def wrapper(n):
            if not isinstance(n, var_type):
                raise TypeError("Only int numbers!")
            return func(n)
        return wrapper
    return decorator

@ensure(int)
def foo(n):
    return n + 1

if __name__ == "__main__":
    print(foo(3))
    print(foo("3"))