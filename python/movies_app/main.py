import pandas as pd
from movies_app import *
from pathlib import Path

BASE_DIR = "./ml-100k"
# df_ratings = pd.read_table('./ml-100k/u.data', header = None,
#                    names = ("user_id", "item_id", "rating", "timestamp"))
#
# df_items = pd.read_csv('./ml-100k/u.item', header = None,
#                        sep="|", usecols=[0, 1], encoding = 'latin-1',
#                        index_col = 0, names = ("movie_id","movie_name"))
#

if __name__ == "__main__":
    movie_name = "toy story"
    loc_prov = LocalMovieProvider(Path(BASE_DIR))
    print(loc_prov.get_movie_data(movie_name))
