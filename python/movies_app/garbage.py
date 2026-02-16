# self.df_ratings = pd.read_table(self.path / 'u.data', header=None,
#                            names=("user_id", "item_id", "rating", "timestamp"))
# self.df_items = pd.read_csv(self.path / 'u.item', header = None,
#                sep="|", usecols=[0, 1], encoding = 'latin-1',
#                index_col = 0, names = ("movie_id","movie_name"))
# self.df_items["year"] = self.df_items['movie_name'].str.extract(r'\((\d{4})\)')
# self.df_items["year"] = pd.to_numeric(self.df_items["year"])
# self.df_items['movie_name'] = self.df_items['movie_name'].str.replace(r'\s*\(\d{4}\)','', regex=True)

