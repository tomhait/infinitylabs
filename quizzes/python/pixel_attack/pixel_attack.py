import argparse

import torch
import torchvision.models as models
from PIL import Image
from torchvision.models import MobileNet_V2_Weights


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

