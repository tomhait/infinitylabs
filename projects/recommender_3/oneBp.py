import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F


def normalize(x):
    return F.normalize(x, p=2, dim=-1)


def build_gender_map():
    return {'M': 0, 'F': 1}


def build_genre_map(movies):
    genres = set()
    for value in movies['genres'].dropna():
        for genre in str(value).split('|'):
            genres.add(genre.lower())
    return {genre: index for index, genre in enumerate(sorted(genres))}


def build_movie_genres_lookup(movies):
    return {
        row['movieId']: '|'.join(g.lower() for g in str(row['genres']).split('|'))
        if pd.notna(row['genres']) else ''
        for _, row in movies[['movieId', 'genres']].iterrows()
    }


def build_genre_mask(movie_map, movies, genre_map=None, movie_genres=None):
    if movies is None or movies.empty or 'genres' not in movies.columns:
        return None

    genre_map = genre_map or build_genre_map(movies)
    if not genre_map:
        return None

    movie_genres = movie_genres or build_movie_genres_lookup(movies)
    n_items = len(movie_map)
    n_genres = len(genre_map)
    mask = np.zeros((n_items, n_genres), dtype=np.float32)

    for movie_id, item_idx in movie_map.items():
        genres_str = movie_genres.get(movie_id, '')
        if not genres_str:
            continue
        for genre in genres_str.split('|'):
            if genre in genre_map:
                mask[item_idx, genre_map[genre]] = 1.0

    return mask


def build_demographic_indices(user_map, users):
    if users is None or users.empty:
        return None

    gender_map = build_gender_map()
    age_values = sorted(users['age'].unique())
    occ_values = sorted(users['occupation'].unique())
    age_map = {value: index for index, value in enumerate(age_values)}
    occ_map = {value: index for index, value in enumerate(occ_values)}

    n_users = len(user_map)
    age_idx = np.zeros(n_users, dtype=np.int64)
    gender_idx = np.zeros(n_users, dtype=np.int64)
    occ_idx = np.zeros(n_users, dtype=np.int64)
    users_by_id = users.set_index('userId')

    for user_id, user_index in user_map.items():
        if user_id not in users_by_id.index:
            continue
        row = users_by_id.loc[user_id]
        age_idx[user_index] = age_map[row['age']]
        gender_idx[user_index] = gender_map.get(row['gender'], 0)
        occ_idx[user_index] = occ_map[row['occupation']]

    return {
        'age_idx': age_idx,
        'gender_idx': gender_idx,
        'occupation_idx': occ_idx,
        'n_ages': len(age_values),
        'n_genders': len(gender_map),
        'n_occupations': len(occ_values),
    }


class DemoEncoder(nn.Module):
    def __init__(
        self,
        n_ages,
        n_genders,
        n_occupations,
        age_idx,
        gender_idx,
        occupation_idx,
        demo_dim=16,
    ):
        super().__init__()
        self.age_embedding = nn.Embedding(n_ages, demo_dim)
        self.gender_embedding = nn.Embedding(n_genders, demo_dim)
        self.occupation_embedding = nn.Embedding(n_occupations, demo_dim)
        self.register_buffer('age_idx', torch.as_tensor(age_idx, dtype=torch.long))
        self.register_buffer('gender_idx', torch.as_tensor(gender_idx, dtype=torch.long))
        self.register_buffer(
            'occupation_idx', torch.as_tensor(occupation_idx, dtype=torch.long)
        )
        self.out_dim = 3 * demo_dim

    def forward(self, user_indices):
        return torch.cat([
            self.age_embedding(self.age_idx[user_indices]),
            self.gender_embedding(self.gender_idx[user_indices]),
            self.occupation_embedding(self.occupation_idx[user_indices]),
        ], dim=-1)


class UserTower(nn.Module):
    def __init__(self, num_users, embedding_dim):
        super().__init__()
        self.embedding = nn.Embedding(num_users, embedding_dim)
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim, 128),
            nn.ReLU(),
            nn.Linear(128, embedding_dim),
        )

    def forward(self, ids):
        return self.mlp(self.embedding(ids))


class ItemTower(nn.Module):
    def __init__(self, num_items, embedding_dim, genre_mask=None, genre_dim=16):
        super().__init__()
        self.id_embedding = nn.Embedding(num_items, embedding_dim)
        self.use_genres = genre_mask is not None and genre_mask.shape[1] > 0
        if self.use_genres:
            num_genres = genre_mask.shape[1]
            self.genre_embedding = nn.Embedding(num_genres, genre_dim)
            self.register_buffer('genre_mask', genre_mask.float())
            mlp_in = embedding_dim + genre_dim
        else:
            self.genre_embedding = None
            mlp_in = embedding_dim
        self.mlp = nn.Sequential(
            nn.Linear(mlp_in, 128),
            nn.ReLU(),
            nn.Linear(128, embedding_dim),
        )

    def forward(self, ids):
        id_vec = self.id_embedding(ids)
        if not self.use_genres:
            return self.mlp(id_vec)

        weights = self.genre_mask[ids]
        genre_vec = weights @ self.genre_embedding.weight
        genre_vec = genre_vec / weights.sum(dim=1, keepdim=True).clamp(min=1.0)
        return self.mlp(torch.cat([id_vec, genre_vec], dim=-1))


class TwoTowerModel(nn.Module):
    def __init__(self, num_users, num_items, embedding_dim=64, genre_mask=None, genre_dim=16):
        super().__init__()
        self.user_tower = UserTower(num_users, embedding_dim)
        self.item_tower = ItemTower(
            num_items, embedding_dim, genre_mask=genre_mask, genre_dim=genre_dim
        )

    def score(self, user_vec, item_ids):
        """Dot product between one user vector and many item ids."""
        item_vec = self.item_tower(item_ids)
        return (normalize(user_vec) * normalize(item_vec)).sum(dim=1)


def default_torch_device():
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def infonce_loss(user_vecs, pos_vecs, neg_vecs, temperature=1.0, margin=0.0):
    """InfoNCE / sampled-softmax loss: classify the positive among negatives.

    When margin > 0, it is added to negative logits so the positive must satisfy
    pos_score > neg_score + margin.
    """
    user_n = normalize(user_vecs)
    pos_n = normalize(pos_vecs)
    neg_n = normalize(neg_vecs)

    pos_scores = (user_n * pos_n).sum(dim=1)
    neg_scores = (neg_n * user_n.unsqueeze(1)).sum(dim=2)
    if margin != 0.0:
        neg_scores = neg_scores + margin
    logits = torch.cat([pos_scores.unsqueeze(1), neg_scores], dim=1)
    if temperature != 1.0:
        logits = logits / temperature

    targets = torch.zeros(logits.size(0), dtype=torch.long, device=logits.device)
    return F.cross_entropy(logits, targets)


class OneBPModel:
    """
    OneBP training on a two-tower model:
    - item tower learns via InfoNCE + backprop
    - user vector moves toward liked items via moving average (no user backprop)
    """

    def __init__(
        self,
        num_dim=64,
        learning_rate=0.01,
        num_epochs=100,
        n_negatives=5,
        beta=0.99,
        temperature=1.0,
        margin=0.0,
        liked_th=4,
        dislike_th=2,
        reg_penalty=0.0,
        batch_size=1024,
        genre_dim=16,
        demo_dim=16,
        history_max_movies=None,
        dislike_frac=0.4,
        hard_neg_frac=0.4,
        hard_neg_top_genres=3,
        random_seed=42,
        verbose=True,
        device=None,
    ):
        self.num_dim = num_dim
        self.lr = learning_rate
        self.num_epochs = num_epochs
        self.n_negatives = n_negatives
        self.beta = beta
        self.temperature = temperature
        self.margin = margin
        self.liked_th = liked_th
        self.dislike_th = dislike_th
        self.reg_penalty = reg_penalty
        self.batch_size = batch_size
        self.genre_dim = genre_dim
        self.demo_dim = demo_dim
        self.history_max_movies = history_max_movies
        self.dislike_frac = dislike_frac
        self.hard_neg_frac = hard_neg_frac
        self.hard_neg_top_genres = hard_neg_top_genres
        self.rng = np.random.default_rng(random_seed)
        self.verbose = verbose
        self.device = device or default_torch_device()

        self.user_map = {}
        self.movie_map = {}
        self.model = None
        self.user_repr = None
        self.demo_encoder = None
        self.user_fuse = None
        self.item_optimizer = None
        self.disliked = None
        self.liked = None
        self.rated = None
        self.hard_neg_arr = None
        self._fitted = False

    def _build_maps(self, user_ids, movie_ids, ratings):
        users = np.sort(np.union1d(user_ids, ratings['userId'].unique()))
        movies = np.sort(np.union1d(movie_ids, ratings['movieId'].unique()))
        self.user_map = {u: i for i, u in enumerate(users)}
        self.movie_map = {m: i for i, m in enumerate(movies)}
        self.n_users = len(users)
        self.n_items = len(movies)

    def _build_side_features(self, users, movies):
        genre_mask = build_genre_mask(self.movie_map, movies)
        demo = build_demographic_indices(self.user_map, users)
        return genre_mask, demo

    def _init_side_feature_modules(self, genre_mask, demo):
        genre_mask_t = (
            torch.from_numpy(genre_mask).to(self.device) if genre_mask is not None else None
        )
        self.model = TwoTowerModel(
            self.n_users,
            self.n_items,
            self.num_dim,
            genre_mask=genre_mask_t,
            genre_dim=self.genre_dim,
        ).to(self.device)

        self.demo_encoder = None
        self.user_fuse = None
        if demo is not None:
            self.demo_encoder = DemoEncoder(
                demo['n_ages'],
                demo['n_genders'],
                demo['n_occupations'],
                demo['age_idx'],
                demo['gender_idx'],
                demo['occupation_idx'],
                demo_dim=self.demo_dim,
            ).to(self.device)
            fuse_in = self.num_dim + self.demo_encoder.out_dim
            self.user_fuse = nn.Linear(fuse_in, self.num_dim).to(self.device)

        if self.verbose:
            if genre_mask is not None:
                n_with_genres = int((genre_mask.sum(axis=1) > 0).sum())
                print(
                    f"OneBP item genres: {genre_mask.shape[1]} genres, "
                    f"{n_with_genres}/{self.n_items} items tagged"
                )
            if demo is not None:
                print(
                    f"OneBP user demographics: "
                    f"{demo['n_ages']} ages, {demo['n_genders']} genders, "
                    f"{demo['n_occupations']} occupations"
                )

    def _compose_user_vectors(self, user_indices, detach_collab=False):
        user_t = torch.as_tensor(user_indices, device=self.device)
        collab = self.user_repr[user_t]
        if detach_collab:
            collab = collab.detach()
        if self.demo_encoder is None:
            return collab
        demo = self.demo_encoder(user_t)
        return self.user_fuse(torch.cat([collab, demo], dim=-1))

    @torch.no_grad()
    def _collab_vector_from_history(self, train_movies):
        train_movies = np.asarray(train_movies)
        if self.history_max_movies is not None and len(train_movies) > self.history_max_movies:
            train_movies = train_movies[-self.history_max_movies:]

        item_ids = [
            self.movie_map[movie_id]
            for movie_id in train_movies
            if movie_id in self.movie_map
        ]
        if not item_ids:
            return None

        item_t = torch.tensor(item_ids, device=self.device, dtype=torch.long)
        item_vecs = normalize(self.model.item_tower(item_t))
        return normalize(item_vecs.mean(dim=0))

    @torch.no_grad()
    def _compose_user_vector_for_inference(self, user_index, train_movies=None):
        collab = None
        if train_movies is not None:
            collab = self._collab_vector_from_history(train_movies)
        if collab is None:
            collab = self.user_repr[user_index]

        if self.demo_encoder is None:
            return collab

        user_t = torch.tensor([user_index], device=self.device)
        demo = self.demo_encoder(user_t)[0]
        return self.user_fuse(torch.cat([collab, demo], dim=-1))

    def _trainable_parameters(self):
        params = list(self.model.item_tower.parameters())
        if self.demo_encoder is not None:
            params.extend(self.demo_encoder.parameters())
        if self.user_fuse is not None:
            params.extend(self.user_fuse.parameters())
        return params

    def _build_negative_pools(self, ratings, genre_mask=None):
        self.disliked = [set() for _ in range(self.n_users)]
        self.liked = [set() for _ in range(self.n_users)]
        self.rated = [set() for _ in range(self.n_users)]

        user_idx = ratings['userId'].map(self.user_map)
        movie_idx = ratings['movieId'].map(self.movie_map)
        valid = user_idx.notna() & movie_idx.notna()
        users = user_idx[valid].astype(np.int64).to_numpy()
        movies = movie_idx[valid].astype(np.int64).to_numpy()
        rating_vals = ratings.loc[valid, 'rating'].to_numpy()

        for u, m, r in zip(users, movies, rating_vals):
            self.rated[u].add(m)
            if r <= self.dislike_th:
                self.disliked[u].add(m)
            if r >= self.liked_th:
                self.liked[u].add(m)

        self.disliked_arr = [
            np.fromiter(s, dtype=np.int64) if s else np.empty(0, dtype=np.int64)
            for s in self.disliked
        ]

        all_items = np.arange(self.n_items, dtype=np.int64)
        self.unrated_arr = []
        self.hard_neg_arr = []
        for u in range(self.n_users):
            rated_u = self.rated[u]
            if len(rated_u) >= self.n_items:
                unrated_mask = np.zeros(self.n_items, dtype=bool)
            else:
                unrated_mask = np.ones(self.n_items, dtype=bool)
                if rated_u:
                    unrated_mask[list(rated_u)] = False
            self.unrated_arr.append(all_items[unrated_mask])

            hard = np.empty(0, dtype=np.int64)
            if genre_mask is not None and self.liked[u]:
                liked_idx = np.fromiter(self.liked[u], dtype=np.int64)
                genre_counts = genre_mask[liked_idx].sum(axis=0)
                if genre_counts.sum() > 0:
                    n_active = int((genre_counts > 0).sum())
                    top_g = min(self.hard_neg_top_genres, n_active)
                    top_genres = np.argsort(genre_counts)[::-1][:top_g]
                    genre_hit = genre_mask[:, top_genres].sum(axis=1) >= min(2, top_g)
                    hard = all_items[unrated_mask & genre_hit]
            self.hard_neg_arr.append(hard)

    def _sample_negatives(self, user_idx, pos_idx):
        n = self.n_negatives
        picks = []

        def take(pool, count):
            if count <= 0 or len(pool) == 0:
                return
            pool = pool[pool != pos_idx]
            if len(pool) == 0:
                return
            k = min(count, len(pool))
            picks.extend(self.rng.choice(pool, size=k, replace=False))

        take(self.disliked_arr[user_idx], int(round(n * self.dislike_frac)))
        take(self.hard_neg_arr[user_idx], int(round(n * self.hard_neg_frac)))

        need = n - len(picks)
        if need > 0:
            unrated = self.unrated_arr[user_idx]
            if len(unrated) > 0:
                unrated = unrated[unrated != pos_idx]
            if len(unrated) > 0:
                replace = len(unrated) < need
                picks.extend(self.rng.choice(unrated, size=need, replace=replace))

        if not picks:
            return np.empty((0,), dtype=np.int64)
        if len(picks) < n:
            extra = self.rng.choice(picks, size=n - len(picks), replace=True)
            picks = list(picks) + list(extra)
        return np.asarray(picks[:n], dtype=np.int64)

    def _sample_negatives_batch(self, user_indices, pos_indices):
        rows = []
        keep_users = []
        keep_items = []
        for u, p in zip(user_indices, pos_indices):
            negs = self._sample_negatives(int(u), int(p))
            if len(negs) == 0:
                continue
            rows.append(negs)
            keep_users.append(u)
            keep_items.append(p)
        if not rows:
            return None, None, None
        return (
            np.asarray(keep_users, dtype=np.int64),
            np.asarray(keep_items, dtype=np.int64),
            np.stack(rows),
        )

    def _train_batch(self, user_idx, pos_idx, neg_idx):
        user_t = torch.as_tensor(user_idx, device=self.device)
        pos_t = torch.as_tensor(pos_idx, device=self.device)
        neg_t = torch.as_tensor(neg_idx.reshape(-1), device=self.device)

        batch_size, n_neg = neg_idx.shape
        user_vecs = self._compose_user_vectors(user_idx, detach_collab=True)
        pos_vecs = self.model.item_tower(pos_t)
        neg_vecs = self.model.item_tower(neg_t).view(batch_size, n_neg, -1)

        loss = infonce_loss(
            user_vecs, pos_vecs, neg_vecs,
            temperature=self.temperature,
            margin=self.margin,
        )

        self.item_optimizer.zero_grad()
        loss.backward()
        self.item_optimizer.step()

        with torch.no_grad():
            new_pos = normalize(self.model.item_tower(pos_t))
            self.user_repr[user_t] = normalize(
                self.beta * self.user_repr[user_t] + (1.0 - self.beta) * new_pos
            )

        return float(loss.item()) * batch_size

    def fit(self, user_ids, movie_ids, ratings, users=None, movies=None):
        user_ids = np.asarray(user_ids)
        movie_ids = np.asarray(movie_ids)
        ratings = ratings[['userId', 'movieId', 'rating']].copy()

        self._build_maps(user_ids, movie_ids, ratings)

        genre_mask, demo = self._build_side_features(users, movies)
        self._build_negative_pools(ratings, genre_mask=genre_mask)
        self._init_side_feature_modules(genre_mask, demo)

        if self.verbose:
            avg_hard = np.mean([len(h) for h in self.hard_neg_arr]) if self.hard_neg_arr else 0
            if genre_mask is not None:
                print(
                    f"OneBP negatives: {self.dislike_frac:.0%} dislikes, "
                    f"{self.hard_neg_frac:.0%} hard (≥2 of top-{self.hard_neg_top_genres} genres, "
                    f"avg pool {avg_hard:.0f}), rest random"
                )

        for p in self.model.user_tower.parameters():
            p.requires_grad = False

        with torch.no_grad():
            all_users = torch.arange(self.n_users, device=self.device)
            self.user_repr = normalize(self.model.user_tower(all_users)).clone()

        weight_decay = self.reg_penalty or 0.0
        self.item_optimizer = torch.optim.Adam(
            self._trainable_parameters(),
            lr=self.lr,
            weight_decay=weight_decay,
        )

        users = np.array([self.user_map[u] for u in user_ids], dtype=np.int64)
        items = np.array([self.movie_map[m] for m in movie_ids], dtype=np.int64)
        self._fitted = True

        for epoch in range(self.num_epochs):
            order = self.rng.permutation(len(users))
            total_loss = 0.0
            steps = 0

            for start in range(0, len(order), self.batch_size):
                batch_idx = order[start : start + self.batch_size]
                batch_users = users[batch_idx]
                batch_items = items[batch_idx]
                batch_users, batch_items, batch_negs = self._sample_negatives_batch(
                    batch_users, batch_items
                )
                if batch_negs is None:
                    continue

                total_loss += self._train_batch(batch_users, batch_items, batch_negs)
                steps += len(batch_users)

            if self.verbose and (
                epoch == 0 or (epoch + 1) % 10 == 0 or epoch + 1 == self.num_epochs
            ):
                print(f"Epoch {epoch + 1}/{self.num_epochs}: loss={total_loss / max(steps, 1):.4f}")

    @torch.no_grad()
    def predict_user_items(self, user_id, movie_ids, train_movies=None):
        if not self._fitted:
            raise ValueError("Call fit() before predict_user_items().")

        movie_ids = np.asarray(movie_ids)
        scores = np.zeros(len(movie_ids), dtype=np.float64)
        if user_id not in self.user_map:
            return scores

        user_vec = self._compose_user_vector_for_inference(self.user_map[user_id], train_movies=train_movies)
        item_ids = []
        positions = []
        for pos, movie_id in enumerate(movie_ids):
            if movie_id in self.movie_map:
                item_ids.append(self.movie_map[movie_id])
                positions.append(pos)

        if not item_ids:
            return scores

        item_t = torch.tensor(item_ids, device=self.device)
        matched = self.model.score(user_vec, item_t).cpu().numpy()
        for pos, score in zip(positions, matched):
            scores[pos] = score
        return scores


def positives_from_ratings(ratings, liked_th=4):
    liked = ratings[ratings['rating'] >= liked_th]
    return liked['userId'].to_numpy(), liked['movieId'].to_numpy()


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    user_ids_pool = np.arange(1, 51)
    movie_ids_pool = rng.integers(1, 81, 80)
    users_df = pd.DataFrame({
        'userId': user_ids_pool,
        'gender': rng.choice(['M', 'F'], 50),
        'age': rng.choice([1, 18, 25, 35, 45, 50, 56], 50),
        'occupation': rng.integers(0, 21, 50),
    })
    movies_df = pd.DataFrame({
        'movieId': np.unique(movie_ids_pool),
        'genres': rng.choice(
            ['Action|Adventure', 'Comedy|Romance', 'Drama', 'Sci-Fi|Action'],
            len(np.unique(movie_ids_pool)),
        ),
    })
    df = pd.DataFrame({
        'userId': rng.integers(1, 51, 2000),
        'movieId': rng.integers(1, 81, 2000),
        'rating': rng.integers(1, 6, 2000),
    }).drop_duplicates(['userId', 'movieId'])

    pos_users, pos_movies = positives_from_ratings(df)
    model = OneBPModel(num_dim=16, num_epochs=20, n_negatives=3, verbose=False)
    model.fit(pos_users, pos_movies, df, users=users_df, movies=movies_df)

    user_id = int(pos_users[0])
    candidates = np.unique(pos_movies[:20])
    user_train = pos_movies[pos_users == user_id][:10]
    scores = model.predict_user_items(user_id, candidates, train_movies=user_train)
    assert scores.shape == (len(candidates),)
    assert np.isfinite(scores).all()
    print("OneBP smoke test passed.")
