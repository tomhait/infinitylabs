import numpy as np

class TwoLayerMLP:
    def __init__(self, input_size, hidden_size, output_size):
        self.weights_input_hidden = np.random.randn(input_size, hidden_size)
        self.weights_hidden_output = np.random.randn(hidden_size, output_size)
        self.bias_hidden = np.zeros((1, hidden_size))
        self.bias_output = np.zeros((1, output_size))

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x))
        return exp_x / exp_x.sum(axis=1, keepdims=True)

    def forward(self, X):
        self.hidden_input = np.dot(X, self.weights_input_hidden) + self.bias_hidden
        self.hidden_output = self.sigmoid(self.hidden_input)
        self.final_input = np.dot(self.hidden_output, self.weights_hidden_output) + self.bias_output
        self.final_output = self.softmax(self.final_input)
        return self.final_output

    def backward(self, X, y, output, learning_rate):
        output_error = output - y
        hidden_error = np.dot(output_error, self.weights_hidden_output.T) * self.hidden_output * (
                    1 - self.hidden_output)

        self.weights_hidden_output -= learning_rate * np.dot(self.hidden_output.T, output_error)
        self.bias_output -= learning_rate * np.sum(output_error, axis=0, keepdims=True)
        self.weights_input_hidden -= learning_rate * np.dot(X.T, hidden_error)
        self.bias_hidden -= learning_rate * np.sum(hidden_error, axis=0, keepdims=True)

    def train(self, X, y, epochs, learning_rate):
        for epoch in range(epochs):
            output = self.forward(X)
            self.backward(X, y, output, learning_rate)
            if (epoch + 1) % 100 == 0:
                loss = -np.sum(y * np.log(output)) / X.shape[0]
                print(f'Epoch {epoch + 1}, Loss: {loss:.4f}')

    def predict(self, X):
        output = self.forward(X)
        return np.argmax(output, axis=1)

class MLP:
    def __init__(self, layer_sizes):
        self.lr = 0.01
        self.layer_sizes = layer_sizes
        self.num_layers = len(layer_sizes) - 1
        self.weights = []
        self.biases = []
        for i in range(self.num_layers):
            fan_in, fan_out = layer_sizes[i], layer_sizes[i + 1]
            self.weights.append(np.random.randn(fan_in, fan_out))
            self.biases.append(np.zeros((1, fan_out)))

    def sigmoid(self, x):
        return 1 / (1 + np.exp(-x))

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x, axis=1, keepdims=True))
        return exp_x / exp_x.sum(axis=1, keepdims=True)

    def forward(self, X):
        self.activations = [X]
        current = X
        for i in range(self.num_layers - 1):
            z = np.dot(current, self.weights[i]) + self.biases[i]
            current = self.sigmoid(z)
            self.activations.append(current)
        z = np.dot(current, self.weights[-1]) + self.biases[-1]
        output = self.softmax(z)
        self.activations.append(output)
        return output

    def backward(self, y, output):
        delta = output - y
        for i in reversed(range(self.num_layers)):
            dW = np.dot(self.activations[i].T, delta)
            db = np.sum(delta, axis=0, keepdims=True)
            if i > 0:
                delta = np.dot(delta, self.weights[i].T) * self.activations[i] * (1 - self.activations[i])
            self.weights[i] -= self.lr * dW
            self.biases[i] -= self.lr * db

    def train(self, X, y, epochs, learning_rate):
        self.lr = learning_rate
        for epoch in range(epochs):
            output = self.forward(X)
            self.backward(y, output)
            if (epoch + 1) % 100 == 0:
                loss = -np.sum(y * np.log(output)) / X.shape[0]
                print(f'Epoch {epoch + 1}, Loss: {loss:.4f}')

    def predict(self, X):
        output = self.forward(X)
        return np.argmax(output, axis=1)