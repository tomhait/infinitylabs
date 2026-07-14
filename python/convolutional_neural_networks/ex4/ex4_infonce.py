import os
import csv
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import matplotlib.pyplot as plt


LFW_ROOT = os.path.join(os.path.dirname(__file__), "../LFW")
IMG_ROOT = os.path.join(LFW_ROOT, "lfw-deepfunneled", "lfw-deepfunneled")
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
EPOCHS = 50
BATCH_SIZE = 32
PATIENCE = 10
TEMPERATURE = 0.07
EMBED_DIM = 128
MODEL_PATH = "../weights/lfw_siamese_infonce.pth"


def image_path(name, num):
    filename = f"{name}_{int(num):04d}.jpg"
    return os.path.join(IMG_ROOT, name, filename)


def load_people(csv_path):
    people = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get("name") or not row.get("images"):
                continue
            n_images = int(row["images"])
            if n_images >= 2:
                people.append((row["name"], n_images))
    return people


def load_match_pairs(csv_path):
    pairs = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append((row["name"], int(row["imagenum1"]), row["name"], int(row["imagenum2"]), 1))
    return pairs


def load_mismatch_pairs(csv_path):
    pairs = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            pairs.append((row[0], int(row[1]), row[2], int(row[3]), 0))
    return pairs


def load_view2_folds(csv_path):
    rows = []
    with open(csv_path, newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            rows.append(row)

    folds = []
    for fold in range(10):
        block = rows[fold * 600:(fold + 1) * 600]
        pairs = []
        for row in block[:300]:
            pairs.append((row[0], int(row[1]), row[0], int(row[2]), 1))
        for row in block[300:]:
            pairs.append((row[0], int(row[1]), row[2], int(row[3]), 0))
        folds.append(pairs)
    return folds


def make_optimizer(model):
    return torch.optim.Adam(
        [
            {"params": model.backbone.parameters(), "lr": 1e-3},
            {"params": model.projector.parameters(), "lr": 1e-3},
        ]
    )


class PairTrainDataset(Dataset):
    def __init__(self, people, transform):
        self.people = people
        self.transform = transform

    def __len__(self):
        return len(self.people)

    def __getitem__(self, idx):
        name, n_images = self.people[idx]
        i, j = random.sample(range(1, n_images + 1), 2)
        img1 = Image.open(image_path(name, i)).convert("RGB")
        img2 = Image.open(image_path(name, j)).convert("RGB")
        return self.transform(img1), self.transform(img2)


class EvalPairDataset(Dataset):
    def __init__(self, pairs, transform):
        self.pairs = pairs
        self.transform = transform

    def __len__(self):
        return len(self.pairs)

    def __getitem__(self, idx):
        name1, num1, name2, num2, label = self.pairs[idx]
        img1 = Image.open(image_path(name1, num1)).convert("RGB")
        img2 = Image.open(image_path(name2, num2)).convert("RGB")
        return self.transform(img1), self.transform(img2), torch.tensor(label, dtype=torch.float32)


class FaceEncoder(nn.Module):
    def __init__(self, embed_dim=128):
        super().__init__()
        backbone = models.resnet18(weights=None)
        backbone.fc = nn.Identity()
        self.backbone = backbone
        self.projector = nn.Sequential(
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Linear(256, embed_dim),
        )

    def forward(self, x):
        x = self.backbone(x)
        x = self.projector(x)
        return F.normalize(x, dim=1)


def info_nce_loss(z1, z2, temperature=0.07):
    logits = z1 @ z2.T / temperature
    labels = torch.arange(z1.size(0), device=z1.device)
    loss_a = F.cross_entropy(logits, labels)
    loss_b = F.cross_entropy(logits.T, labels)
    return (loss_a + loss_b) / 2


def train_epoch(model, loader, opt):
    model.train()
    total_loss = 0.0
    for img1, img2 in loader:
        img1 = img1.to(DEVICE)
        img2 = img2.to(DEVICE)
        z1 = model(img1)
        z2 = model(img2)
        loss = info_nce_loss(z1, z2, TEMPERATURE)
        opt.zero_grad()
        loss.backward()
        opt.step()
        total_loss += loss.item()
    return total_loss / len(loader)


@torch.no_grad()
def pair_scores(model, loader):
    model.eval()
    scores = []
    labels = []
    for img1, img2, label in loader:
        img1 = img1.to(DEVICE)
        img2 = img2.to(DEVICE)
        z1 = model(img1)
        z2 = model(img2)
        sim = (z1 * z2).sum(dim=1).cpu()
        scores.append(sim)
        labels.append(label if torch.is_tensor(label) else torch.tensor(label))
    return torch.cat(scores), torch.cat(labels).float()


def best_threshold_accuracy(scores, labels):
    best_acc = 0.0
    best_t = 0.0
    for t in torch.linspace(scores.min(), scores.max(), 101):
        preds = (scores >= t).float()
        acc = (preds == labels).float().mean().item()
        if acc > best_acc:
            best_acc = acc
            best_t = t.item()
    return best_t, best_acc


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


if __name__ == "__main__":
    train_people = load_people(os.path.join(LFW_ROOT, "peopleDevTrain.csv"))
    val_pairs = load_match_pairs(os.path.join(LFW_ROOT, "matchpairsDevTest.csv"))
    val_pairs += load_mismatch_pairs(os.path.join(LFW_ROOT, "mismatchpairsDevTest.csv"))

    train_loader = DataLoader(
        PairTrainDataset(train_people, transform),
        batch_size=BATCH_SIZE,
        shuffle=True,
        drop_last=True,
    )
    val_loader = DataLoader(EvalPairDataset(val_pairs, transform), batch_size=BATCH_SIZE)

    model = FaceEncoder(EMBED_DIM).to(DEVICE)
    opt = make_optimizer(model)

    print("device:", DEVICE, flush=True)
    print("backbone: ResNet-18 from scratch + InfoNCE", flush=True)
    print("train people with >=2 images:", len(train_people), flush=True)
    print("DevTest val pairs:", len(val_pairs), flush=True)
    print("InfoNCE face verification on LFW", flush=True)

    os.makedirs("../weights", exist_ok=True)
    os.makedirs("../outputs", exist_ok=True)

    train_losses = []
    val_accs = []
    best_val_acc = 0.0
    epochs_no_improve = 0
    best_threshold = 0.0
    best_epoch = 1

    for epoch in range(EPOCHS):
        loss = train_epoch(model, train_loader, opt)
        scores, labels = pair_scores(model, val_loader)
        threshold, val_acc = best_threshold_accuracy(scores, labels)
        train_losses.append(loss)
        val_accs.append(val_acc)
        print(
            f"epoch {epoch + 1}/{EPOCHS} "
            f"infonce_loss={loss:.4f} val_acc={100 * val_acc:.2f}% thr={threshold:.3f}",
            flush=True,
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_threshold = threshold
            best_epoch = epoch + 1
            epochs_no_improve = 0
            torch.save(
                {"model": model.state_dict(), "threshold": best_threshold},
                MODEL_PATH,
            )
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= PATIENCE:
                print(f"early stopping at epoch {epoch + 1}", flush=True)
                break

    ckpt = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
    model.load_state_dict(ckpt["model"])
    best_threshold = ckpt["threshold"]
    print(f"loaded best model from epoch {best_epoch}", flush=True)
    print(f"saved model to {MODEL_PATH}", flush=True)

    scores, labels = pair_scores(model, val_loader)
    val_preds = (scores >= best_threshold).float()
    val_acc = (val_preds == labels).float().mean().item()
    print(f"threshold={best_threshold:.3f}  DevTest pair accuracy={100 * val_acc:.2f}%", flush=True)

    plt.figure(figsize=(8, 4))
    plt.subplot(1, 2, 1)
    plt.plot(range(1, len(train_losses) + 1), train_losses, label="InfoNCE")
    plt.xlabel("epoch")
    plt.ylabel("loss")
    plt.title("Train InfoNCE loss")
    plt.legend()
    plt.subplot(1, 2, 2)
    plt.plot(range(1, len(val_accs) + 1), val_accs, label="val acc")
    plt.xlabel("epoch")
    plt.ylabel("accuracy")
    plt.title("Validation pair accuracy")
    plt.legend()
    plt.tight_layout()
    plt.savefig("outputs/lfw_infonce.png", dpi=150)
    plt.show()
    print("saved outputs/lfw_infonce.png", flush=True)

    examples = next(iter(val_loader))
    img1, img2, labels = examples
    img1, img2 = img1[:5].to(DEVICE), img2[:5].to(DEVICE)
    with torch.no_grad():
        sim = (model(img1) * model(img2)).sum(dim=1).cpu()
    for i in range(5):
        pred = int(sim[i] >= best_threshold)
        print(
            f"true={'same' if labels[i] == 1 else 'diff'}  "
            f"pred={'same' if pred == 1 else 'diff'}  sim={sim[i]:.3f}",
            flush=True,
        )

    print(
        f"View 2 10-fold with train_epochs={best_epoch}, "
        f"threshold={best_threshold:.3f}",
        flush=True,
    )
    all_people = load_people(os.path.join(LFW_ROOT, "people.csv"))
    folds = load_view2_folds(os.path.join(LFW_ROOT, "pairs.csv"))
    fold_accs = []

    for fold_idx, fold_pairs in enumerate(folds):
        test_names = set()
        for name1, _, name2, _, _ in fold_pairs:
            test_names.add(name1)
            test_names.add(name2)

        fold_train_people = [
            (name, n_images)
            for name, n_images in all_people
            if name not in test_names and n_images >= 2
        ]
        fold_train_loader = DataLoader(
            PairTrainDataset(fold_train_people, transform),
            batch_size=BATCH_SIZE,
            shuffle=True,
            drop_last=True,
        )
        fold_test_loader = DataLoader(
            EvalPairDataset(fold_pairs, transform),
            batch_size=BATCH_SIZE,
        )

        fold_model = FaceEncoder(EMBED_DIM).to(DEVICE)
        fold_opt = make_optimizer(fold_model)
        for epoch in range(best_epoch):
            loss = train_epoch(fold_model, fold_train_loader, fold_opt)
            print(
                f"fold {fold_idx + 1}/10 epoch {epoch + 1}/{best_epoch} "
                f"loss={loss:.4f}",
                flush=True,
            )

        fold_scores, fold_labels = pair_scores(fold_model, fold_test_loader)
        fold_preds = (fold_scores >= best_threshold).float()
        fold_acc = (fold_preds == fold_labels).float().mean().item()
        fold_accs.append(fold_acc)
        print(f"fold {fold_idx + 1}/10 accuracy={100 * fold_acc:.2f}%", flush=True)

    fold_accs = torch.tensor(fold_accs)
    print(
        f"View 2 10-fold accuracy: {100 * fold_accs.mean():.2f}% "
        f"+/- {100 * fold_accs.std(unbiased=True):.2f}%",
        flush=True,
    )
