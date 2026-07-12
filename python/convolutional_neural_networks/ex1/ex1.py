import os
import glob
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader


def rgb_to_ycbcr(x):
    device = x.device
    imgs = (x.detach().cpu().permute(0, 2, 3, 1).numpy() * 255).clip(0, 255).astype(np.uint8)
    y_list, cb_list, cr_list = [], [], []
    for img in imgs:
        ycrcb = cv2.cvtColor(img, cv2.COLOR_RGB2YCrCb).astype(np.float32) / 255.0
        y_list.append(ycrcb[:, :, 0])
        cr_list.append(ycrcb[:, :, 1])
        cb_list.append(ycrcb[:, :, 2])
    y = torch.from_numpy(np.stack(y_list))[:, None].to(device)
    cb = torch.from_numpy(np.stack(cb_list))[:, None].to(device)
    cr = torch.from_numpy(np.stack(cr_list))[:, None].to(device)
    return y, cb, cr


def ycbcr_to_rgb(y, cb, cr):
    device = y.device
    ycrcb = torch.cat([y, cr, cb], dim=1).detach().cpu().permute(0, 2, 3, 1).numpy()
    ycrcb = (ycrcb * 255).clip(0, 255).astype(np.uint8)
    rgb_list = []
    for img in ycrcb:
        rgb = cv2.cvtColor(img, cv2.COLOR_YCrCb2RGB).astype(np.float32) / 255.0
        rgb_list.append(rgb)
    return torch.from_numpy(np.stack(rgb_list)).permute(0, 3, 1, 2).to(device)


class ShrinkNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Conv2d(16, 3, kernel_size=3, padding=1),
        )

    def forward(self, x):
        return F.avg_pool2d(x, 2) + self.net(x)


class SRCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=9, padding=4),
            nn.ReLU(),
            nn.Conv2d(64, 32, kernel_size=5, padding=2),
            nn.ReLU(),
            nn.Conv2d(32, 1, kernel_size=5, padding=2),
        )

    def forward(self, x):
        return self.net(x)


class ESPCN(nn.Module):
    def __init__(self, scale=2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(1, 64, kernel_size=5, padding=2),
            nn.Tanh(),
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.Tanh(),
            nn.Conv2d(32, 1 * (scale ** 2), kernel_size=3, padding=1),
            nn.PixelShuffle(scale),
        )

    def forward(self, x):
        return self.net(x)


class ResBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(channels, channels, kernel_size=3, padding=1),
        )

    def forward(self, x):
        return x + self.block(x)


class EDSR(nn.Module):
    def __init__(self, scale=2, n_blocks=4, n_feats=64):
        super().__init__()
        self.head = nn.Sequential(
            nn.Conv2d(1, n_feats, kernel_size=3, padding=1),
        )
        self.body = nn.Sequential(
            *[ResBlock(n_feats) for _ in range(n_blocks)],
            nn.Conv2d(n_feats, n_feats, kernel_size=3, padding=1),
        )
        self.tail = nn.Sequential(
            nn.Conv2d(n_feats, n_feats * (scale ** 2), kernel_size=3, padding=1),
            nn.PixelShuffle(scale),
            nn.Conv2d(n_feats, 1, kernel_size=3, padding=1),
        )

    def forward(self, x):
        x = self.head(x)
        x = x + self.body(x)
        x = self.tail(x)
        return x


class PetSRDataset(Dataset):
    def __init__(self, root, scale=2, patch=96, max_images=300):
        paths = []
        for folder in ["Cat", "Dog"]:
            paths += glob.glob(os.path.join(root, folder, "*.jpg"))
        self.paths = paths[:max_images]
        self.scale = scale
        self.patch = patch

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        for _ in range(20):
            try:
                img = Image.open(self.paths[idx]).convert("RGB")
                w, h = img.size
                if w < self.patch or h < self.patch:
                    img = img.resize((max(w, self.patch), max(h, self.patch)))
                    w, h = img.size
                left = np.random.randint(0, w - self.patch + 1)
                top = np.random.randint(0, h - self.patch + 1)
                hr = img.crop((left, top, left + self.patch, top + self.patch))
                hr = torch.from_numpy(np.array(hr)).float().permute(2, 0, 1) / 255.0
                lr = F.interpolate(
                    hr.unsqueeze(0),
                    scale_factor=1 / self.scale,
                    mode="bicubic",
                    align_corners=False,
                ).squeeze(0)
                return lr, hr
            except Exception:
                idx = (idx + 1) % len(self.paths)
        hr = torch.zeros(3, self.patch, self.patch)
        lr = torch.zeros(3, self.patch // self.scale, self.patch // self.scale)
        return lr, hr


def train_model(model, loader, name, mode, epochs=3, lr=1e-3, shrink_model=None):
    model = model.to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    model.train()
    for epoch in range(epochs):
        total = 0.0
        for low, high in loader:
            high = high.to(DEVICE)
            if mode == "shrink":
                x = high
                y = F.interpolate(high, scale_factor=1 / SCALE, mode="bicubic", align_corners=False)
            elif mode == "srcnn":
                with torch.no_grad():
                    shrunk = shrink_model(high)
                y_hr, _, _ = rgb_to_ycbcr(high)
                y_s, _, _ = rgb_to_ycbcr(shrunk)
                x = F.interpolate(y_s, scale_factor=SCALE, mode="bicubic", align_corners=False)
                y = y_hr
            elif mode == "sr":
                with torch.no_grad():
                    shrunk = shrink_model(high)
                y_hr, _, _ = rgb_to_ycbcr(high)
                y_s, _, _ = rgb_to_ycbcr(shrunk)
                x, y = y_s, y_hr
            else:
                raise ValueError(mode)

            pred = model(x)
            loss = loss_fn(pred, y)
            opt.zero_grad()
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"{name} epoch {epoch + 1}/{epochs} loss={total / len(loader):.4f}")
    path = os.path.join(WEIGHTS_DIR, f"{name}.pth")
    torch.save(model.state_dict(), path)
    print("saved", path)
    return model


def load_model(model, name):
    path = os.path.join(WEIGHTS_DIR, f"{name}.pth")
    model.load_state_dict(torch.load(path, map_location=DEVICE))
    model = model.to(DEVICE)
    model.eval()
    print("loaded", path)
    return model


def tensor_to_image(t):
    t = t.detach().cpu().clamp(0, 1).squeeze(0)
    arr = (t.permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    return Image.fromarray(arr)


def restore_color(y_pred, shrunk):
    _, cb, cr = rgb_to_ycbcr(shrunk)
    cb = F.interpolate(cb, scale_factor=SCALE, mode="bicubic", align_corners=False)
    cr = F.interpolate(cr, scale_factor=SCALE, mode="bicubic", align_corners=False)
    return ycbcr_to_rgb(y_pred, cb, cr)


def demo(models):
    img = Image.open(DEMO_IMG).convert("RGB")
    w, h = img.size
    w = w - (w % SCALE)
    h = h - (h % SCALE)
    img = img.crop((0, 0, w, h))
    hr = torch.from_numpy(np.array(img)).float().permute(2, 0, 1).unsqueeze(0) / 255.0
    hr = hr.to(DEVICE)

    os.makedirs(OUT_DIR, exist_ok=True)
    with torch.no_grad():
        shrunk = models["shrink"](hr)
        y_s, _, _ = rgb_to_ycbcr(shrunk)
        y_up = F.interpolate(y_s, scale_factor=SCALE, mode="bicubic", align_corners=False)
        srcnn_out = restore_color(models["srcnn"](y_up), shrunk)
        espcn_out = restore_color(models["espcn"](y_s), shrunk)
        edsr_out = restore_color(models["edsr"](y_s), shrunk)

    panels = [
        (hr, "Original"),
        (shrunk, "ShrinkNet"),
        (srcnn_out, "SRCNN"),
        (espcn_out, "ESPCN"),
        (edsr_out, "EDSR"),
    ]

    pil_images = []
    titles = []
    for t, title in panels:
        pil = tensor_to_image(t)
        pil.save(os.path.join(OUT_DIR, title.lower().replace(" ", "_") + ".png"))
        pil_images.append(pil)
        titles.append(title)

    widths = [im.size[0] for im in pil_images]
    heights = [im.size[1] for im in pil_images]
    max_h = max(heights)
    gap = 10
    total_w = sum(widths) + gap * (len(pil_images) - 1)
    canvas = Image.new("RGB", (total_w, max_h), (255, 255, 255))
    x = 0
    for im in pil_images:
        y = (max_h - im.size[1]) // 2
        canvas.paste(im, (x, y))
        x += im.size[0] + gap

    fig_h = 4
    fig_w = fig_h * total_w / max_h
    fig, ax = plt.subplots(figsize=(fig_w, fig_h + 0.6))
    ax.imshow(canvas)
    ax.axis("off")

    x = 0
    for im, title, iw, ih in zip(pil_images, titles, widths, heights):
        ax.text(x + iw / 2, -max_h * 0.04, f"{title}\n{iw}x{ih}", ha="center", va="bottom", fontsize=10)
        x += iw + gap

    plt.tight_layout()
    plot_path = os.path.join(OUT_DIR, "nature.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.show()
    print("demo saved to", OUT_DIR)
    print("comparison plot:", plot_path)


SCALE = 2
ROOT = os.path.join(os.path.dirname(__file__), "PetImages")
WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "weights")
OUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
DEMO_IMG = os.path.join(os.path.dirname(__file__), "test_images", "test_dog2.jpg")
MAX_IMAGES = 300
EPOCHS = 3
BATCH_SIZE = 16
RETRAIN = True
DEVICE = torch.device("mps" if torch.backends.mps.is_available() else "cpu")

os.makedirs(WEIGHTS_DIR, exist_ok=True)

shrink = ShrinkNet()
srcnn = SRCNN()
espcn = ESPCN(scale=SCALE)
edsr = EDSR(scale=SCALE, n_blocks=4, n_feats=32)

print("device:", DEVICE)

if RETRAIN:
    dataset = PetSRDataset(ROOT, scale=SCALE, patch=96, max_images=MAX_IMAGES)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    shrink = train_model(shrink, loader, "shrink", mode="shrink", epochs=EPOCHS)
    shrink.eval()
    srcnn = train_model(srcnn, loader, "srcnn", mode="srcnn", epochs=EPOCHS, shrink_model=shrink)
    espcn = train_model(espcn, loader, "espcn", mode="sr", epochs=EPOCHS, shrink_model=shrink)
    edsr = train_model(edsr, loader, "edsr", mode="sr", epochs=EPOCHS, shrink_model=shrink)
else:
    shrink = load_model(shrink, "shrink")
    srcnn = load_model(srcnn, "srcnn")
    espcn = load_model(espcn, "espcn")
    edsr = load_model(edsr, "edsr")

demo({"shrink": shrink.eval(), "srcnn": srcnn.eval(), "espcn": espcn.eval(), "edsr": edsr.eval()})
