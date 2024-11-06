import logging
from hydra import compose
import os
import torch
import torchvision.transforms as transforms
from PIL import Image
from huggingface_hub import hf_hub_download
from src.inference.model import SiameseNetwork
from src.database.repository import PapyrusEmbeddingEntity
from src.database.postgres import Postgres
import uuid
from datetime import datetime

cfg = compose(config_name='config')

log = logging.getLogger(__name__)


transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)


def load_model(device):
    model_file = hf_hub_download(repo_id='veerav96/papyrusNet', filename='resnet18_checkpoint_RUN10.pth')
    checkpoint = torch.load(model_file, map_location=device)
    model_state_dict = checkpoint['model_state_dict']
    model = SiameseNetwork().to(device)
    model.load_state_dict(model_state_dict)
    model.eval()
    return model


def compute_embedding(model, image_path, device):
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0)  # Add batch dimension
    with torch.no_grad():
        embedding = model.forward_one(image_tensor.to(device)).squeeze(0).cpu().numpy()
    return embedding


def get_url_from_filename(filename: str) -> str:
    """
    Constructs url for papyrus from filename
    Example: For '123_p_g_323.jpg', the url would be https://digi.ub.uni-heidelberg.de/diglit/p_g_124_b/0001/_image.
    """
    if '_' not in filename:
        raise ValueError('Filename must contain an underscore.')

    parts = filename.split('_', 1)  # Split the filename at the first underscore
    image_name = parts[1].rsplit('.', 1)[0]  # Remove the file extension
    url = f'https://digi.ub.uni-heidelberg.de/diglit/{image_name}/0001/_image'
    return url


def process_images_bulk_insert(model, folder_path, device, batch_size=30):
    database = Postgres.from_config(cfg)
    entities = []

    for image_file in os.listdir(folder_path):
        image_path = os.path.join(folder_path, image_file)

        if image_file.endswith(('.jpg', '.jpeg', '.png')):  # Filter by image files
            embedding = compute_embedding(model, image_path, device)
            url = get_url_from_filename(image_file)

            entity = PapyrusEmbeddingEntity(
                id=uuid.uuid4(),
                url=url,
                created_at=datetime.now(),
                modified_at=datetime.now(),
                embedding=embedding.tolist(),
            )
            entities.append(entity)

            if len(entities) >= batch_size:
                database.papyrus_embedding_repository.bulk_insert(entities)
                entities.clear()

    if entities:
        database.papyrus_embedding_repository.bulk_insert(entities)


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = load_model(device)
    folder_path = 'PATH-TO-ANCHOR-IMAGES'
    process_images_bulk_insert(model, folder_path, device, batch_size=30)


if __name__ == '__main__':
    main()
