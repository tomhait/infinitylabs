import numpy as np
from statistics import mode
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from datetime import datetime
from functools import wraps

def func_timer(func):
    @wraps(func)
    def wrap_func(*args, **kargs):
        start = datetime.now()
        res = func(*args, **kargs)
        time_elapsed = (datetime.now() - start).total_seconds()
        print(f"The {func.__name__} took {time_elapsed} seconds")
        return res
    return wrap_func

class NaiveKNN:
    def __init__(self, k=5):
        self.k = k

    def fit(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train

    @func_timer
    def predict(self, X_test):
       return np.array([self._single_predict(x) for x in X_test])

    def _single_predict(self, x):
        distances = np.linalg.norm(self.X_train - x, axis = 1)
        k_nearest_ind = np.argsort(distances)[:self.k]
        k_nearest_labels = [self.y_train[i] for i in k_nearest_ind]
        return mode(k_nearest_labels)

class PcaKNN:
    def __init__(self, k=5, n_comp=2):
        self.k = k
        self.pca = PCA(n_components=n_comp)

    def fit(self, X_train, y_train):
        X_scaled = StandardScaler().fit_transform(X_train)
        self.X_train = self.pca.fit_transform(X_scaled)
        self.y_train = y_train

    @func_timer
    def predict(self, X_test):
        X_scaled = StandardScaler().fit_transform(X_test)
        X_test_reduced = self.pca.transform(X_scaled)
        return np.array([self._single_predict(x) for x in X_test_reduced])

    def _single_predict(self, x):
        distances = np.linalg.norm(self.X_train - x, axis = 1)
        k_nearest_ind = np.argsort(distances)[:self.k]
        k_nearest_labels = [self.y_train[i] for i in k_nearest_ind]
        return mode(k_nearest_labels)

if __name__ == "__main__":
    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(iris.data, iris.target, test_size=0.2)

    knn = NaiveKNN()
    knn.fit(X_train, y_train)
    preds = knn.predict(X_test)

    accuracy = np.mean(preds == y_test)
    print(f"Accuracy: {accuracy * 100:.2f}%")

    knn = PcaKNN(n_comp=1)
    knn.fit(X_train, y_train)
    preds = knn.predict(X_test)

    accuracy = np.mean(preds == y_test)
    print(f"Accuracy: {accuracy * 100:.2f}%")