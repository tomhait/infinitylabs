import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, transforms
import matplotlib.pyplot as plt


class FashionCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 128),
            nn.ReLU(),
            nn.Linear(128, 10),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


def run_epoch(model, loader, loss_fn, opt=None):
    is_train = opt is not None
    model.train(is_train)
    total_loss = 0.0
    correct = 0
    total = 0
    for images, labels in loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)
        if is_train:
            opt.zero_grad()
        with torch.set_grad_enabled(is_train):
            preds = model(images)
            loss = loss_fn(preds, labels)
            if is_train:
                loss.backward()
                opt.step()
        total_loss += loss.item()
        correct += (preds.argmax(1) == labels).sum().item()
        total += labels.size(0)
    return total_loss / len(loader), 100 * correct / total

DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
EPOCHS = 30
BATCH_SIZE = 128
PATIENCE = 5
MODEL_PATH = "weights/fashion_cnn.pth"

transform = transforms.Compose([
    transforms.ToTensor(),
])

full_train = datasets.FashionMNIST(
    root="data",
    train=True,
    download=True,
    transform=transform,
)
test_data = datasets.FashionMNIST(
    root="data",
    train=False,
    download=True,
    transform=transform,
)

train_data, val_data = random_split(full_train, [50000, 10000])
train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True)
val_loader = DataLoader(val_data, batch_size=BATCH_SIZE)
test_loader = DataLoader(test_data, batch_size=BATCH_SIZE)

model = FashionCNN().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.CrossEntropyLoss()

print("device:", DEVICE)
print("training Fashion MNIST with vanilla CNN")

os.makedirs("weights", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

train_losses = []
val_losses = []
best_val_loss = float("inf")
epochs_no_improve = 0
stopped_epoch = EPOCHS

for epoch in range(EPOCHS):
    train_loss, train_acc = run_epoch(model, train_loader, loss_fn, opt)
    val_loss, val_acc = run_epoch(model, val_loader, loss_fn)
    train_losses.append(train_loss)
    val_losses.append(val_loss)
    print(
        f"epoch {epoch + 1}/{EPOCHS} "
        f"train_loss={train_loss:.4f} train_acc={train_acc:.2f}% "
        f"val_loss={val_loss:.4f} val_acc={val_acc:.2f}%"
    )

    if val_loss < best_val_loss:
        best_val_loss = val_loss
        epochs_no_improve = 0
    else:
        epochs_no_improve += 1
        if epochs_no_improve >= PATIENCE:
            stopped_epoch = epoch + 1
            print(f"early stopping at epoch {stopped_epoch}")
            break

plt.figure()
epochs_ran = range(1, len(train_losses) + 1)
plt.plot(epochs_ran, train_losses, label="train")
plt.plot(epochs_ran, val_losses, label="validation")
plt.xlabel("epoch")
plt.ylabel("loss")
plt.title("Fashion MNIST train vs validation loss")
plt.legend()
plt.tight_layout()
plt.savefig("outputs/fashion_loss.png", dpi=150)
plt.show()
print("saved outputs/fashion_loss.png")

print(f"retraining on train+val for {stopped_epoch - PATIENCE} epochs")
full_loader = DataLoader(full_train, batch_size=BATCH_SIZE, shuffle=True)
model = FashionCNN().to(DEVICE)
opt = torch.optim.Adam(model.parameters(), lr=1e-3)

for epoch in range(stopped_epoch - PATIENCE):
    train_loss, train_acc = run_epoch(model, full_loader, loss_fn, opt)
    print(
        f"retrain epoch {epoch + 1}/{stopped_epoch - PATIENCE} "
        f"loss={train_loss:.4f} acc={train_acc:.2f}%"
    )

torch.save(model.state_dict(), MODEL_PATH)
print(f"saved model to {MODEL_PATH}")

test_loss, test_acc = run_epoch(model, test_loader, loss_fn)
print(f"test loss={test_loss:.4f}  test accuracy={test_acc:.2f}%")
