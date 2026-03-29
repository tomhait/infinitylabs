import numpy as np

class LogisticRegressionL1:
    EPSILON = 1e-15

    def __init__(self, lr=0.01, lambda_reg=0.1, n_iter=1000, tol=1e-4):
        self.lr = lr
        self.lambda_reg = lambda_reg
        self.n_iter = n_iter
        self.tol = tol
        self.weights = None
        self.bias = 0

    def _sigmoid(self, z):
        return 1 / (1 + np.exp(-np.clip(z, -500, 500)))

    def _compute_loss(self, X, y):
        m = X.shape[0]
        y_hat = self._sigmoid(np.dot(X, self.weights) + self.bias)
        loss = -np.mean(y * np.log(y_hat + self.EPSILON) + (1-y) * np.log(1 - y_hat + self.EPSILON))
        l1_penalty = (self.lambda_reg / m) * np.sum(np.abs(self.weights))
        return loss + l1_penalty

    def _get_gradients(self, X, y):
        m = X.shape[0]
        y_hat = self._sigmoid(np.dot(X, self.weights) + self.bias)
        error = y_hat - y
        dw = (1 / m) * np.dot(X.T, error) + (self.lambda_reg / m) * np.sign(self.weights)
        db = (1 / m) * np.sum(error)
        return dw, db

    def fit(self, X, y):
        self.weights = np.zeros(X.shape[1])
        self.bias = 0

        last_loss = float('inf')

        for i in range(self.n_iter):
            dw, db = self._get_gradients(X, y)

            self.weights -= self.lr * dw
            self.bias -= self.lr * db

            loss = self._compute_loss(X, y)

            if i % 200 == 0:
                print(f"Iteration {i} | Loss: {loss:.4f}")

            if abs(last_loss - loss) < self.tol:
                print(f"Early stopping at iteration {i}")
                break
            last_loss = loss

    def _predict_prob(self, X):
        linear_model = np.dot(X, self.weights) + self.bias
        return self._sigmoid(linear_model)

    def predict(self, X, th=0.5):
        return [1 if i > th else 0 for i in self._predict_prob(X)]
