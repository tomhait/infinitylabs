import ssl
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.datasets import fetch_openml

ssl._create_default_https_context = ssl._create_unverified_context

mnist = fetch_openml('mnist_784', version=1, as_frame=False)

X, y = mnist["data"], mnist["target"]

print(f"Data shape and classes: {X.shape}, {np.unique(y)}")

scaler = StandardScaler()
pca = PCA(n_components=0.95)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

X_train_reduced = pca.fit_transform(scaler.fit_transform(X_train))
X_test_reduced = pca.transform(scaler.transform(X_test))

knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train_reduced, y_train)
accuracy = knn.score(X_test_reduced, y_test)

print(f"MNIST Accuracy with PCA: {accuracy:.2%}")