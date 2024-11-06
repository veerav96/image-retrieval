from fastapi import UploadFile
import litserve as ls
import torch
import torchvision.transforms as transforms
from PIL import Image
from src.inference.model import SiameseNetwork
from huggingface_hub import hf_hub_download
import logging

log = logging.getLogger(__name__)

transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


class SiameseLitAPI(ls.LitAPI):
    def setup(self, device):
        model_file = hf_hub_download(repo_id='veerav96/papyrusNet', filename='resnet18_checkpoint_RUN10.pth')
        checkpoint = torch.load(model_file, map_location=device)
        model_state_dict = checkpoint['model_state_dict']
        self.model = SiameseNetwork().to(device)
        self.model.load_state_dict(model_state_dict)
        self.model.eval()
        self.device = device

    def decode_request(self, request: UploadFile):
        image = Image.open(request.file).convert('RGB')
        log.info('Image opened and converted to RGB: %s', image.size)
        image = transform(image)
        return image.unsqueeze(0)  # Add batch dimension

    def predict(self, image_tensor):
        with torch.no_grad():
            log.info('Input image tensor shape: %s', image_tensor.shape)
            embedding = self.model.forward_one(image_tensor.to(self.device))
            embedding = embedding.squeeze(0).cpu().numpy()
        return {'embedding': embedding.tolist()}

    def encode_response(self, output):
        return output


if __name__ == '__main__':
    api = SiameseLitAPI()
    server = ls.LitServer(api, accelerator='auto')
    server.run(port=8001)
