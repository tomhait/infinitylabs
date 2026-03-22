import numpy as np
from statistics import mode
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

class NaiveKNN:
    def __init__(self, k=5):
        self.k = k

    def fit(self, X_train, y_train):
        self.X_train = X_train
        self.y_train = y_train

    def predict(self, X_test):
       return np.array([self._single_predict(x) for x in X_test])

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
