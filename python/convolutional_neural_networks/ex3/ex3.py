import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split, Subset, ConcatDataset
from torchvision import datasets, transforms, models
import matplotlib.pyplot as plt


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


def make_vgg(num_classes, head_only=True):
    model = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)
    model.classifier[6] = nn.Linear(4096, num_classes)
    for param in model.features.parameters():
        param.requires_grad = False
    if not head_only:
        for param in model.features[17:].parameters():
            param.requires_grad = True
    return model.to(DEVICE)


def make_optimizer(model, head_only=True):
    if head_only:
        return torch.optim.Adam(
            filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3
        )
    return torch.optim.Adam(
        [
            {"params": model.features[17:].parameters(), "lr": 1e-5},
            {"params": model.classifier.parameters(), "lr": 1e-4},
        ]
    )


def train_with_early_stopping(model, opt, train_loader, val_loader, loss_fn, epochs, patience, title):
    train_losses = []
    val_losses = []
    best_val_loss = float("inf")
    epochs_no_improve = 0
    stopped_epoch = epochs

    for epoch in range(epochs):
        train_loss, train_acc = run_epoch(model, train_loader, loss_fn, opt)
        val_loss, val_acc = run_epoch(model, val_loader, loss_fn)
        train_losses.append(train_loss)
        val_losses.append(val_loss)
        print(
            f"epoch {epoch + 1}/{epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.2f}% "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.2f}%",
            flush=True,
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                stopped_epoch = epoch + 1
                print(f"early stopping at epoch {stopped_epoch}", flush=True)
                break

    plt.figure()
    xs = range(1, len(train_losses) + 1)
    plt.plot(xs, train_losses, label="train")
    plt.plot(xs, val_losses, label="validation")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    return stopped_epoch, train_losses, val_losses


DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
DATA_DIR = os.path.join(os.path.dirname(__file__), "../PlantVillage", "PlantVillage")
EPOCHS = 20
FT_EPOCHS = 10
BATCH_SIZE = 32
PATIENCE = 3
MAX_IMAGES = 3000
MODEL_PATH = "../weights/vgg16_plantvillage.pth"
FT_MODEL_PATH = "../weights/vgg16_plantvillage_finetuned.pth"

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

print("loading dataset...", flush=True)
dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
num_classes = len(dataset.classes)
class_names = dataset.classes

if len(dataset) > MAX_IMAGES:
    g = torch.Generator().manual_seed(42)
    indices = torch.randperm(len(dataset), generator=g)[:MAX_IMAGES].tolist()
    full_data = Subset(dataset, indices)
else:
    full_data = dataset

n_total = len(full_data)
n_test = int(0.1 * n_total)
n_val = int(0.1 * n_total)
n_train = n_total - n_val - n_test
train_data, val_data, test_data = random_split(
    full_data, [n_train, n_val, n_test], generator=torch.Generator().manual_seed(0)
)

train_loader = DataLoader(train_data, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
val_loader = DataLoader(val_data, batch_size=BATCH_SIZE, num_workers=0)
test_loader = DataLoader(test_data, batch_size=BATCH_SIZE, num_workers=0)
trainval_data = ConcatDataset([train_data, val_data])
trainval_loader = DataLoader(trainval_data, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

loss_fn = nn.CrossEntropyLoss()
os.makedirs("../weights", exist_ok=True)
os.makedirs("../outputs", exist_ok=True)

print("device:", DEVICE, flush=True)
print("classes:", num_classes, class_names, flush=True)
print("samples: train", n_train, "val", n_val, "test", n_test, flush=True)

print("stage 1: head-only", flush=True)
model = make_vgg(num_classes, head_only=True)
opt = make_optimizer(model, head_only=True)
stopped_epoch, _, _ = train_with_early_stopping(
    model, opt, train_loader, val_loader, loss_fn, EPOCHS, PATIENCE,
    "PlantVillage VGG16 head-only train vs validation loss",
)
plt.savefig("outputs/plantvillage_loss.png", dpi=150)
plt.show()
print("saved outputs/plantvillage_loss.png", flush=True)

retrain_epochs = max(1, stopped_epoch - PATIENCE)
print(f"retraining head-only on train+val for {retrain_epochs} epochs", flush=True)
model = make_vgg(num_classes, head_only=True)
opt = make_optimizer(model, head_only=True)
for epoch in range(retrain_epochs):
    train_loss, train_acc = run_epoch(model, trainval_loader, loss_fn, opt)
    print(
        f"retrain epoch {epoch + 1}/{retrain_epochs} "
        f"loss={train_loss:.4f} acc={train_acc:.2f}%",
        flush=True,
    )
torch.save(model.state_dict(), MODEL_PATH)
print(f"saved model to {MODEL_PATH}", flush=True)

head_test_loss, head_test_acc = run_epoch(model, test_loader, loss_fn)
print(f"head-only test loss={head_test_loss:.4f}  acc={head_test_acc:.2f}%", flush=True)

print("stage 2: fine-tune last conv block + new classifier head from scratch", flush=True)
model = make_vgg(num_classes, head_only=False)
opt = make_optimizer(model, head_only=False)

ft_stopped_epoch, _, _ = train_with_early_stopping(
    model, opt, train_loader, val_loader, loss_fn, FT_EPOCHS, PATIENCE,
    "PlantVillage VGG16 fine-tune train vs validation loss",
)
plt.savefig("outputs/plantvillage_finetune_loss.png", dpi=150)
plt.show()
print("saved outputs/plantvillage_finetune_loss.png", flush=True)

ft_retrain_epochs = max(1, ft_stopped_epoch - PATIENCE)
print(f"retraining fine-tune on train+val for {ft_retrain_epochs} epochs", flush=True)
model = make_vgg(num_classes, head_only=False)
opt = make_optimizer(model, head_only=False)
for epoch in range(ft_retrain_epochs):
    train_loss, train_acc = run_epoch(model, trainval_loader, loss_fn, opt)
    print(
        f"ft retrain epoch {epoch + 1}/{ft_retrain_epochs} "
        f"loss={train_loss:.4f} acc={train_acc:.2f}%",
        flush=True,
    )

torch.save(model.state_dict(), FT_MODEL_PATH)
print(f"saved model to {FT_MODEL_PATH}", flush=True)

ft_test_loss, ft_test_acc = run_epoch(model, test_loader, loss_fn)
print(f"fine-tune test loss={ft_test_loss:.4f}  acc={ft_test_acc:.2f}%", flush=True)
print(f"head-only test acc={head_test_acc:.2f}%  fine-tune test acc={ft_test_acc:.2f}%", flush=True)

images, labels = next(iter(test_loader))
images = images[:5].to(DEVICE)
with torch.no_grad():
    preds = model(images).argmax(1).cpu()
for i in range(5):
    print(f"true={class_names[labels[i]]}  pred={class_names[preds[i]]}", flush=True)
