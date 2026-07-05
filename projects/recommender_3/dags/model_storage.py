import os
import pickle

MODEL_DIR = os.path.join(os.path.dirname(__file__), 'saved_models')
PRODUCTION_MODEL_PATH = os.path.join(MODEL_DIR, 'nb.pkl')
LEGACY_PRODUCTION_MODEL_PATHS = (
    os.path.join(MODEL_DIR, 'production_model.pkl'),
    os.path.join(MODEL_DIR, 'nb.pkl'),
)
CANDIDATE_MODEL_PATH = os.path.join(MODEL_DIR, 'candidate_model.pkl')
MODEL_PATH = PRODUCTION_MODEL_PATH

PRODUCTION_FM_KWARGS = {
    'num_dim': 8,
    'num_epochs': 10,
    'learning_rate': 0.05,
    'batch_size': 2048,
    'train_sample_frac': 1.0,
}

PRODUCTION_ONEBP_KWARGS = {
    'num_dim': 64,
    'num_epochs': 10,
    'learning_rate': 0.01,
    'n_negatives': 5,
    'beta': 0.99,
    'temperature': 1.0,
    'liked_th': 4,
    'dislike_th': 2,
    'batch_size': 1024,
    'train_sample_frac': 1.0,
    'dislike_frac': 0.4,
    'hard_neg_frac': 0.4,
    'hard_neg_top_genres': 3,
}

SUPPORTED_CANDIDATE_MODELS = ('factorization_machine', 'onebp')


def ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def get_trained_model_path(model_name, model_dir=None):
    base_dir = model_dir or MODEL_DIR
    return os.path.join(base_dir, f'{model_name}.pkl')


def save_trained_model(model_name, artifact, model_dir=None):
    base_dir = model_dir or MODEL_DIR
    os.makedirs(base_dir, exist_ok=True)
    path = get_trained_model_path(model_name, base_dir)
    with open(path, 'wb') as f:
        pickle.dump(artifact, f)
    print(f"Saved trained model to {path}.")


def load_trained_model(model_name, model_dir=None):
    path = get_trained_model_path(model_name, model_dir)
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return pickle.load(f)


def save_trained_models(artifacts, model_dir=None, best_model=None):
    base_dir = model_dir or MODEL_DIR
    os.makedirs(base_dir, exist_ok=True)
    for model_name, artifact in artifacts.items():
        save_trained_model(model_name, artifact, model_dir=base_dir)
    if best_model is not None:
        manifest = {'best_model': best_model, 'models': list(artifacts.keys())}
        manifest_path = os.path.join(base_dir, 'manifest.pkl')
        with open(manifest_path, 'wb') as f:
            pickle.dump(manifest, f)
        print(f"Saved manifest to {manifest_path} (best_model={best_model}).")


def load_manifest(model_dir=None):
    base_dir = model_dir or MODEL_DIR
    manifest_path = os.path.join(base_dir, 'manifest.pkl')
    if not os.path.exists(manifest_path):
        return None
    with open(manifest_path, 'rb') as f:
        return pickle.load(f)


def get_production_model_path():
    if os.path.exists(PRODUCTION_MODEL_PATH):
        return PRODUCTION_MODEL_PATH
    for path in LEGACY_PRODUCTION_MODEL_PATHS:
        if os.path.exists(path):
            return path
    return None


def save_production_model(artifact):
    ensure_model_dir()
    with open(PRODUCTION_MODEL_PATH, 'wb') as f:
        pickle.dump(artifact, f)
    print(f"Production model saved to {PRODUCTION_MODEL_PATH}.")


def save_candidate_model(artifact):
    ensure_model_dir()
    with open(CANDIDATE_MODEL_PATH, 'wb') as f:
        pickle.dump(artifact, f)
    print(f"Candidate model saved to {CANDIDATE_MODEL_PATH}.")


def load_candidate_model():
    if not os.path.exists(CANDIDATE_MODEL_PATH):
        return None
    with open(CANDIDATE_MODEL_PATH, 'rb') as f:
        return pickle.load(f)


def promote_candidate_to_production():
    artifact = load_candidate_model()
    if artifact is None:
        raise FileNotFoundError(f"No candidate model at {CANDIDATE_MODEL_PATH}.")
    save_production_model(artifact)
    os.remove(CANDIDATE_MODEL_PATH)
    print(f"Promoted candidate model to {PRODUCTION_MODEL_PATH}.")


def load_production_model():
    path = get_production_model_path()
    if path is None:
        return None
    with open(path, 'rb') as f:
        return pickle.load(f)


def get_production_model_type():
    artifact = load_production_model()
    if artifact is None:
        return 'naive_bayes'
    return artifact.get('model_type', 'naive_bayes')
