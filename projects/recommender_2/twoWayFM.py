import numpy as np

class TwoWayFM:
    """
    Models a Factorization Machine
    if reg_penalty is not zero - performs L2 regularization
    """
    def __init__(self, num_dim, reg_penalty = 0.01, num_epochs = 100,
                 learning_rate = 0.05, batch_size=32, random_seed=42, verbose = True):
        self.k = num_dim
        self.reg_penalty = 2 * reg_penalty if reg_penalty is not None else 0.0
        self.epoch = num_epochs
        self.lr = learning_rate
        self.batch_size = batch_size
        self.random_seed = random_seed
        self.rng = np.random.default_rng(random_seed)
        self.verbose = verbose
        self.std = 1
        self.mean = 0

        self.w0 = 0.0
        self.w = None
        self.V = None

    def _setup(self, num_features):
        self.w0 = 0.0
        self.w = np.zeros(num_features)
        self.V = self.rng.normal(0.0, 0.1, (num_features, self.k))

    def _standardize(self, X, is_train = False):
        if is_train:
            self.std = np.std(X, axis=0)
            self.mean = np.mean(X, axis=0)
        X_standardized = (X - self.mean) / (self.std + 1e-8)
        return X_standardized

    def _forward_batch(self, X_batch):
        """
        Computes forward batch for a mini batch
        """
        linear_terms = self.w0 + np.dot(X_batch, self.w)
        sum_v_x = np.dot(X_batch, self.V)
        sum_v2_x2 = np.dot(X_batch ** 2, self.V ** 2)
        interaction_terms = 0.5 * np.sum(sum_v_x ** 2 - sum_v2_x2, axis=1)
        y_hat = linear_terms + interaction_terms
        return y_hat, sum_v_x

    def _gradient(self, X_batch, y_batch):
        """
        Performs gradient descent on a mini-batch
        """
        actual_batch_size = X_batch.shape[0]
        y_hat, sum_v_x = self._forward_batch(X_batch)
        errors = 2 * (y_hat - y_batch)
        grad_w0 = np.mean(errors) + self.reg_penalty * self.w0

        grad_w = np.dot(errors, X_batch) / actual_batch_size + self.reg_penalty * self.w
        term1 = np.dot(X_batch.T, errors[:, np.newaxis] * sum_v_x)

        term2 = self.V * np.dot(errors, X_batch ** 2)[:, np.newaxis]

        grad_V = (term1 - term2) / actual_batch_size + self.reg_penalty * self.V

        self.w0 -= self.lr * grad_w0
        self.w -= self.lr * grad_w
        self.V -= self.lr * grad_V

    def fit(self, X, y):
        """
        Trains FM model using mini-batch gradient descent
        """
        num_samples, num_features = X.shape
        self._setup(num_features)
        X = self._standardize(X, is_train = True)
        for epoch in range(self.epoch):
            if epoch % 10 == 0 and self.verbose:
                print(f"Epoch number: {epoch}")
            indices = np.arange(num_samples)
            self.rng.shuffle(indices)
            X_shuffled = X[indices]
            y_shuffled = y[indices]

            for start_idx in range(0, num_samples, self.batch_size):
                end_idx = min(start_idx + self.batch_size, num_samples)
                X_batch = X_shuffled[start_idx:end_idx]
                y_batch = y_shuffled[start_idx:end_idx]
                self._gradient(X_batch, y_batch)


    def predict(self, X):
        if self.w is None:
            self._setup(X.shape[1])
        X = self._standardize(X)
        y_hat, _ = self._forward_batch(X)
        return y_hat

if __name__ == "__main__":
    num_samples = 100
    num_features = 5
    X_train = np.random.normal(0, 1, (num_samples, num_features))
    true_w0 = 1.5
    true_w = np.array([0.5, -1.0, 2.0, 0.0, -0.5])
    true_interactions = X_train[:, 0] * X_train[:, 1] * 3.0
    y_train = true_w0 + np.dot(X_train, true_w) + true_interactions + np.random.normal(0, 0.1, num_samples)

    model = TwoWayFM(num_dim=2, reg_penalty=0.01, num_epochs=200,
                     learning_rate=0.02, batch_size=10, verbose = False)

    initial_preds = model.predict(X_train[:5])
    print("Before Training:")
    print(f"Target values:      {np.round(y_train[:5], 3)}")
    print(f"Initial predictions:{np.round(initial_preds, 3)}")

    print("\nTraining the model...")
    model.fit(X_train, y_train)

    post_preds = model.predict(X_train[:5])
    print("\nAfter Training:")
    print(f"Target values:      {np.round(y_train[:5], 3)}")
    print(f"Final predictions:  {np.round(post_preds, 3)}")

    mse = np.mean((model.predict(X_train) - y_train) ** 2)
    print(f"\nFinal Training MSE: {mse:.4f}")

    assert mse < 0.5, "Test Failed ..."
    print("Test Passed!")
