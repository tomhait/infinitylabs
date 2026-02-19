class Movie:
    """ Holds the Movie's metadata"""
    def __init__(self, title, id):
        self.title = title
        self.id = id
        self.year = "--"
        self.movielens_rating = "--"
        self.omdb_rating = "--"
        self.metascore = "--"
        self.int_movie_db = "--"
        self.rotten_tomatoes = "--"
        self.matacritic = "--"
        self.poster_url = "--"

    def add_movielens_rating(self, rating):
        self.movielens_rating = rating

    def add_omdb_rating(self, rating):
        self.omdb_rating = rating

    def add_metascore(self, metascore):
        self.metascore = metascore

    def add_ratings(self, ratings):
        """ Parses OMDb ratings"""
        for rate in ratings:
            if rate['Source'] == "Internet Movie Database":
                self.int_movie_db = rate.get("Value")
            elif rate['Source'] == "Rotten Tomatoes":
                self.rotten_tomatoes = rate.get("Value")
            elif rate['Source'] == "Metacritic":
                self.matacritic = rate.get("Value")

    def add_poster_url(self, poster_url):
        self.poster_url = poster_url

    def get_poster_url(self):
        return self.poster_url

    def get_int_movie_rate(self):
        return self.int_movie_db

    def get_rotten_rate(self):
        return self.rotten_tomatoes

    def get_metacritic_rate(self):
        return self.matacritic

    def set_title(self, title):
        self.title = title

    def get_imdb_id(self):
        return self.id

    def get_local_rating(self):
        return self.movielens_rating

    def get_omdb_rating(self):
        return self.omdb_rating

    def get_title(self):
        return self.title

    def set_year(self, year):
        self.year = int(year)

    def get_year(self):
        return self.year

    @classmethod
    def from_string(cls, title):
        return cls(title, "NA")

    @classmethod
    def from_tuple(cls, title_value):
        return cls(title_value[0], title_value[1])
