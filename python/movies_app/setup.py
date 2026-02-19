""" Script to download MovieLens 100k dataset from Kaggle"""
import subprocess
import zipfile

try:
    result = subprocess.run(["bash", "./setup.sh"], check=True, capture_output=True, text=True)
    print("Download successful!")
except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e.stderr}")

zip_path = "./movielens-100k.zip"

with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(".")