import kagglehub
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder

path = kagglehub.dataset_download("yasserh/titanic-dataset")

print("Path to dataset files:", path)

df = pd.read_csv(path+"/Titanic-Dataset.csv")

print(df.count())

# Fill missing age with median
df['Age'] = df['Age'].fillna(df['Age'].median())

df['Sex'] = LabelEncoder().fit_transform(df['Sex'])

# Numerical feature selection
features = ['Pclass', 'Sex', 'Age', 'SibSp', 'Parch', 'Fare']
X = df[features]
y = df['Survived']

# Standardization
X_scaled = StandardScaler().fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)
knn = KNeighborsClassifier(n_neighbors=5)
knn.fit(X_train, y_train)

print(f"Titanic Survival Accuracy: {knn.score(X_test, y_test):.2%}")