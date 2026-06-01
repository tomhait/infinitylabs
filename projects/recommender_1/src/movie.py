class Movie:
    """ Holds the Movie's metadata"""
    def __init__(self, title, movie_id):
        self.title = title
        self.movie_id = movie_id
        self.year = "--"
        self.movielens_rating = "--"
        self.omdb_rating = "--"
        self.metascore = "--"
        self.int_movie_db = "--"
        self.rotten_tomatoes = "--"
        self.matacritic = "--"
        self.poster_url = "--"

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

    def set_title(self, title):
        self.title = title

    def get_imdb_id(self):
        return self.movie_id

    def get_title(self):
        return self.title

    def set_year(self, year):
        self.year = int(year)

    def get_year(self):
        return self.year

    def get_all_ratings(self):
        return {'movielens': self.movielens_rating,
                'omdb': self.omdb_rating,
                'metascore': self.metascore,
                'rotten': self.rotten_tomatoes,
                'metacritic': self.matacritic,
                "internet": self.int_movie_db
                }

    @classmethod
    def from_string(cls, title):
        return cls(title, "NA")

    @classmethod
    def from_tuple(cls, title_value):
        return cls(title_value[0], title_value[1])
