import mysql.connector
import json
import glob
from functools import wraps
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

def create_customer_table(cursor):
    create_query = """
    CREATE TABLE IF NOT EXISTS customers (
        `Index` INT PRIMARY KEY,
        `Customer Id` VARCHAR(50),
        `First Name` VARCHAR(100),
        `Last Name` VARCHAR(100),
        `Company` VARCHAR(255),
        `City` VARCHAR(100),
        `Country` VARCHAR(100),
        `Phone 1` VARCHAR(50),
        `Phone 2` VARCHAR(50),
        `Email` VARCHAR(255),
        `Subscription Date` DATE,
        `Website` VARCHAR(255)
    );
    """
    cursor.execute(create_query)

def worker_load_batch(file_chunk, db_config, columns):
    temp_config = db_config.copy()
    db_name = temp_config.pop('database')
    db = mysql.connector.connect(**temp_config)
    cursor = db.cursor()

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    cursor.execute(f"USE {db_name}")

    create_customer_table(cursor)

    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cursor.execute("SET UNIQUE_CHECKS = 0;")

    cols_str = ", ".join([f"`{col}`" for col in columns])
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT IGNORE INTO customers ({cols_str}) VALUES ({placeholders})"

    batch = []
    for file_path in file_chunk:
        with open(file_path, 'r') as f:
            data = json.load(f)
            records = data if isinstance(data, list) else [data]

            for record in records:
                row = tuple(record.get(col) for col in columns)
                batch.append(row)

    cursor.executemany(insert_sql, batch)
    db.commit()
    cursor.close()
    db.close()

@func_timer
def dispatch_workers(json_dir, db_config, columns, func):
    json_files = glob.glob(f"{json_dir}/*.json")
    chunks = [json_files[i:i + 1000] for i in range(0, len(json_files), 1000)]
    with ProcessPoolExecutor() as executor:
        executor.map(func, chunks, [db_config] * len(chunks), [columns] * len(chunks))

def verify_data(db_config):
    db = mysql.connector.connect(**db_config)
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM customers")
    count = cursor.fetchone()[0]
    print(f"Total rows in 'customers' table: {count}")

    cursor.execute("SELECT * FROM customers LIMIT 5")
    rows = cursor.fetchall()

    print("\nFirst 5 records:")
    for row in rows:
        print(row)

    cursor.close()
    db.close()

if __name__ == '__main__':
    db_config = {
        'host': '127.0.0.1',
        'port': 3307,
        'user': 'root',
        'password': '',
        'database': 'customers_db',
        'allow_local_infile': True
    }
    json_dir = './output'
    columns = ['Index', 'Customer Id', 'First Name', 'Last Name',
               'Company', 'City', 'Country', 'Phone 1', 'Phone 2'
        , 'Email', 'Subscription Date', 'Website']
    dispatch_workers(json_dir,db_config, columns, worker_load_batch)
    verify_data(db_config)