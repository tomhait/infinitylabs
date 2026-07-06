import torch
from torch import nn, optim
from torchvision import datasets, transforms
import matplotlib.pyplot as plt


class AE(nn.Module):
    def __init__(self, latent_dim = 9):
        super().__init__()
        self.latent_dim = latent_dim
        self.encoder = nn.Sequential(
            nn.Linear(784, 128), nn.ReLU(),
            nn.Linear(128, 64), nn.ReLU(),
            nn.Linear(64, 36), nn.ReLU(),
            nn.Linear(36, 18), nn.ReLU(),
            nn.Linear(18, self.latent_dim),
        )
        self.decoder = nn.Sequential(
            nn.Linear(self.latent_dim, 18), nn.ReLU(),
            nn.Linear(18, 36), nn.ReLU(),
            nn.Linear(36, 64), nn.ReLU(),
            nn.Linear(64, 128), nn.ReLU(),
            nn.Linear(128, 784), nn.Sigmoid(),
        )

    def forward(self, x):
        return self.decoder(self.encoder(x))


def evaluate(model, loader, criterion, device):
    model.eval()
    total, n = 0.0, 0
    with torch.no_grad():
        for images, _ in loader:
            x = images.view(-1, 784).to(device)
            total += criterion(model(x), x).item()
            n += 1
    return total / n


def analyze_latents(model, loader, criterion, device):
    model.eval()
    latent_dim = model.latent_dim
    latents = []
    with torch.no_grad():
        for images, _ in loader:
            latents.append(model.encoder(images.view(-1, 784).to(device)).cpu())
    z = torch.cat(latents).numpy()
    print(f"\nLatent stats: mean={z.mean():.3f}, std={z.std():.3f}")

    images, _ = next(iter(loader))
    x = images[:5].view(-1, 784).to(device)
    with torch.no_grad():
        z = model.encoder(x)

    sigmas = [0, 0.1, 0.5, 1.0]
    fig, axes = plt.subplots(len(sigmas), 5, figsize=(8, len(sigmas) * 1.5))
    for row, s in enumerate(sigmas):
        with torch.no_grad():
            recon = model.decoder(z + s * torch.randn_like(z))
        print(f"sigma={s:.1f}  mse={criterion(recon, x).item():.6f}")
        for col in range(5):
            axes[row, col].imshow(recon[col].cpu().numpy().reshape(28, 28), cmap='gray')
            axes[row, col].axis('off')
    plt.savefig(f'latent_noise_{latent_dim}.png', bbox_inches='tight', dpi=300)
    plt.show()


def train(latent_dim = 9):
    transform = transforms.ToTensor()
    full_train = datasets.FashionMNIST("./data", train=True, download=True, transform=transform)
    test_set = datasets.FashionMNIST("./data", train=False, download=True, transform=transform)
    train_set, val_set = torch.utils.data.random_split(full_train, [50000, 10000])

    loader = lambda ds, shuffle: torch.utils.data.DataLoader(
        ds, batch_size=32, shuffle=shuffle, num_workers=4
    )
    train_loader = loader(train_set, True)
    val_loader = loader(val_set, False)
    test_loader = loader(test_set, False)

    device = torch.device("mps" if torch.mps.is_available() else "cpu")
    model = AE(latent_dim=latent_dim).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-8)
    print(device)

    train_losses, val_losses, epochs = [], [], 20
    for epoch in range(epochs):
        model.train()
        batch_losses = []
        for images, _ in train_loader:
            x = images.view(-1, 784).to(device)
            loss = criterion(model(x), x)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            batch_losses.append(loss.item())
        train_losses.append(sum(batch_losses) / len(batch_losses))
        val_losses.append(evaluate(model, val_loader, criterion, device))
        print(f"Epoch {epoch + 1}/{epochs}  train={train_losses[-1]:.6f}  val={val_losses[-1]:.6f}")

    test_loss = evaluate(model, test_loader, criterion, device)
    print(f"Test loss: {test_loss:.6f}")

    plt.style.use('fivethirtyeight')
    plt.figure(figsize=(8, 5))
    plt.plot(range(1, epochs + 1), train_losses, label='Train')
    plt.plot(range(1, epochs + 1), val_losses, label='Validation')
    plt.xlabel('Epoch')
    plt.ylabel('MSE Loss')
    plt.title(f'Test loss: {test_loss:.6f}')
    plt.legend()
    plt.savefig(f'loss_{latent_dim}.png', bbox_inches='tight', dpi=300)
    plt.show()

    images, _ = next(iter(test_loader))
    x = images[:10].view(-1, 784).to(device)
    with torch.no_grad():
        recon = model(x)
    fig, axes = plt.subplots(2, 10, figsize=(10, 3))
    for i in range(10):
        axes[0, i].imshow(x[i].cpu().numpy().reshape(28, 28), cmap='gray')
        axes[0, i].axis('off')
        axes[1, i].imshow(recon[i].cpu().numpy().reshape(28, 28), cmap='gray')
        axes[1, i].axis('off')
    plt.savefig(f'test_before_after_{latent_dim}.png', bbox_inches='tight', dpi=300)
    plt.show()

    analyze_latents(model, test_loader, criterion, device)


if __name__ == '__main__':
    train(latent_dim=9)
