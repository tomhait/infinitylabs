import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import wraps
from datetime import datetime
import shutil
import csv
import json

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

def create_csv_copy(copy_index, csv_file):
    shutil.copyfile(csv_file, f'output/customers-100.{copy_index}.csv')

def parse_to_json(copy_index):
    csv_file = f"output/customers-100.{copy_index}.csv"
    json_file = f"output/customers-100.{copy_index}.json"
    with open(csv_file, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        data = list(csv_reader)

    with open(json_file, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4)

@func_timer
def main():
    csv_file = "./customers-100.csv"
    os.makedirs('output', exist_ok = True)

    n_copies = 10000
    with ProcessPoolExecutor() as executor:
        for i in range(1, n_copies+1):
            executor.submit(create_csv_copy, i, csv_file)
        for i in range(1, n_copies+1):
            executor.submit(parse_to_json, i)

if __name__ == '__main__':
    main()