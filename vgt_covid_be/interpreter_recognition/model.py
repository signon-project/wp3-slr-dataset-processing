import torch.nn
from torchvision.models import resnet50, resnet18


class Classifier(torch.nn.Module):
    def __init__(self):
        super().__init__()

        resnet = resnet18()
        self.resnet = torch.nn.Sequential(*list(resnet.children())[:-1])
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(512, 1)
        )

    def forward(self, x):
        z = self.resnet(x).squeeze()
        y = self.classifier(z)
        return torch.sigmoid(y.squeeze())
