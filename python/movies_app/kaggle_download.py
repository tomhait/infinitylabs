import kagglehub

# Download latest version
path = kagglehub.dataset_download("abhikjha/movielens-100k")

print("Path to dataset files:", path)