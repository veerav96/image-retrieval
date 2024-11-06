import torch.nn as nn
import torchvision.models as models
import torch.nn.functional as F


class SiameseNetwork(nn.Module):
    def __init__(self):
        super(SiameseNetwork, self).__init__()

        self.base_model = models.resnet18(pretrained=True)

        # Modify the fully connected layer to output a 128-dimensional embedding
        num_ftrs = self.base_model.fc.in_features
        self.base_model.fc = nn.Linear(num_ftrs, 128)

    def forward_one(self, x):
        # Pass input through the base model
        return self.base_model(x)

    def forward(self, input1, input2=None):
        if input2 is None:
            # If only one input is provided, return a single embedding
            embedding = self.forward_one(input1)
            return F.normalize(embedding, p=2, dim=1)  # L2 normalization
        else:
            # If two inputs are provided, return embeddings for both
            embedding1 = self.forward_one(input1)
            embedding2 = self.forward_one(input2)
            return F.normalize(embedding1, p=2, dim=1), F.normalize(embedding2, p=2, dim=1)


# Function to initialize the model
def initialize_model():
    return SiameseNetwork()
