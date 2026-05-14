import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from datetime import datetime
import shutil

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

def write_to_json(copy_index, df):
    filename = f"output/customers-100.{copy_index}.json"
    if copy_index == 1:
        df.to_json(filename, orient='records', indent=4)
    else:
        shutil.copyfile('output/customers-100.1.json', filename)

@func_timer
def main():
    df = pd.read_csv('customers-100.csv')
    os.makedirs('output', exist_ok = True)

    n_copies = 10000
    with ThreadPoolExecutor() as executor:
        for i in range(1, n_copies+1):
            executor.submit(write_to_json, i, df)

if __name__ == '__main__':
    main()