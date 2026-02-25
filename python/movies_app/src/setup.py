""" Script to download MovieLens 100k dataset from Kaggle"""
import os
import subprocess
import zipfile

zip_filename = "movielens-100k.zip"

command = ["curl","-L", "-o", zip_filename,
  "https://www.kaggle.com/api/v1/datasets/download/abhikjha/movielens-100k"]

try:
    result = subprocess.run(command, check=True, capture_output=True,
                            text=True)
    print("Download successful!")
except subprocess.CalledProcessError as e:
    print(f"Error occurred: {e.stderr}")

with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
    zip_ref.extractall("../")
    if os.path.exists(zip_filename):
        os.remove(zip_filename)
        print(f"Temporary file '{zip_filename}' has been deleted.")