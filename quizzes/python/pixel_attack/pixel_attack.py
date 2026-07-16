import argparse

import matplotlib.pyplot as plt
import torch
import torchvision.models as models
from PIL import Image
from torchvision.models import MobileNet_V2_Weights

MEAN = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
STD = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)


def tensor_to_image(tensor):
    image = tensor.squeeze(0).detach().cpu()
    image = (image * STD + MEAN).clamp(0, 1)
    return image.permute(1, 2, 0).numpy()


parser = argparse.ArgumentParser(description="FGSM pixel attack on MobileNet V2")
parser.add_argument("picture", help="path to an input image")
args = parser.parse_args()

model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.IMAGENET1K_V1)
model.eval()

weights = MobileNet_V2_Weights.IMAGENET1K_V1
preprocess = weights.transforms()
categories = weights.meta["categories"]

img = Image.open(args.picture).convert("RGB")
x = preprocess(img).unsqueeze(0)
x.requires_grad_(True)

with torch.no_grad():
    logits = model(x)
pred = logits.argmax(1).item()
print(categories[pred])

criterion = torch.nn.CrossEntropyLoss()
target = torch.tensor([pred])

logits = model(x)
loss = criterion(logits, target)
loss.backward()

eps = 0.03
x_adv = (x + eps * x.grad.sign()).detach()

with torch.no_grad():
    adv_pred = model(x_adv).argmax(1).item()
print("clean:", categories[pred], "→ adv:", categories[adv_pred])

fig, axes = plt.subplots(1, 2, figsize=(10, 5))
axes[0].imshow(tensor_to_image(x))
axes[0].set_title(f"Before: {categories[pred]}")
axes[0].axis("off")

axes[1].imshow(tensor_to_image(x_adv))
axes[1].set_title(f"After: {categories[adv_pred]}")
axes[1].axis("off")

fig.suptitle("FGSM attack on MobileNet V2")
fig.tight_layout()
plt.show()

