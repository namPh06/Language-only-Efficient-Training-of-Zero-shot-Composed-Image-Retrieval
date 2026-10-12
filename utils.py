from typing import Optional, Tuple, List

import math
import torch
import torch.nn.functional as F
from transformers import CLIPVisionModelWithProjection
from torch.utils.data import DataLoader
from torch.utils.data import Dataset
from tqdm import tqdm

from data_utils import collate_fn
from models import Phi


if torch.cuda.is_available():
    device = torch.device("cuda")
    dtype = torch.float16
else:
    device = torch.device("cpu")
    dtype = torch.float32


@torch.no_grad()
def extract_image_features(dataset: Dataset, clip_model: CLIPVisionModelWithProjection, batch_size: Optional[int] = 32,
                           num_workers: Optional[int] = 10) -> Tuple[torch.Tensor, List[str]]:
    """
    Extracts image features from a dataset using a CLIP model.
    """
    # Create data loader
    loader = DataLoader(dataset=dataset, batch_size=batch_size,
                        num_workers=num_workers, pin_memory=True, collate_fn=collate_fn)

    index_features = []
    index_names = []
    try:
        print(f"extracting image features {dataset.__class__.__name__} - {dataset.split}")
    except Exception as e:
        pass

    # Extract features
    for batch in tqdm(loader):
        if batch is None:
            continue
        images = batch.get('image')
        names = batch.get('image_name')
        if images is None:
            images = batch.get('reference_image')
        if names is None:
            names = batch.get('reference_name')

        images = images.to(clip_model.device)
        with torch.no_grad():
            batch_features = clip_model(pixel_values=images.to(clip_model.dtype)).image_embeds #.encode_image(images)
            index_features.append(batch_features.cpu())
            index_names.extend(names)

    if not index_features:
        raise ValueError("Dataset contains no usable images")
    index_features = torch.vstack(index_features)
    return index_features, index_names


def contrastive_loss(v1: torch.Tensor, v2: torch.Tensor, temperature: float) -> torch.Tensor:
    # NT-Xent in log space, excluding self similarities from the denominator.
    if v1.ndim != 2 or v1.shape != v2.shape or not len(v1) or not v1.shape[1]:
        raise ValueError('Contrastive inputs must have the same nonempty N x D shape')
    if v1.device != v2.device or not torch.isfinite(v1).all() or not torch.isfinite(v2).all():
        raise ValueError('Contrastive inputs must be finite and on the same device')
    if not math.isfinite(float(temperature)) or temperature <= 0:
        raise ValueError('Temperature must be finite and positive')
    work_dtype = torch.float64 if torch.float64 in (v1.dtype, v2.dtype) else torch.float32
    joint = torch.cat((F.normalize(v1.to(work_dtype), dim=1), F.normalize(v2.to(work_dtype), dim=1)))
    logits = (joint @ joint.T) / temperature
    if not torch.isfinite(logits).all():
        raise ValueError("Temperature is too small for the tensor precision")
    count = len(joint)
    logits = logits.masked_fill(torch.eye(count, dtype=torch.bool, device=joint.device), -torch.inf)
    indices = torch.arange(count, device=joint.device)
    positives = (indices + len(v1)) % count
    return (torch.logsumexp(logits, dim=1) - logits[indices, positives]).mean()



@torch.no_grad()
def extract_pseudo_tokens_with_phi(clip_model: CLIPVisionModelWithProjection, phi: Phi, dataset: Dataset, args) -> Tuple[torch.Tensor, List[str]]:
    """
    Extracts pseudo tokens from a dataset using a CLIP model and a phi model
    """
    data_loader = DataLoader(dataset=dataset, batch_size=32, num_workers=10, pin_memory=False,
                             collate_fn=collate_fn)
    predicted_tokens = []
    names_list = []
    print(f"Extracting tokens using phi model")
    for batch in tqdm(data_loader):
        if batch is None:
            continue
        images = batch.get('image')
        names = batch.get('image_name')
        if images is None:
            images = batch.get('reference_image')
        if names is None:
            names = batch.get('reference_name')

        images = images.to(clip_model.device)
        image_features = clip_model(pixel_values=images.to(clip_model.dtype)).image_embeds
        if args.l2_normalize:
            image_features = F.normalize(image_features, dim=-1)
        phi_parameter = next(phi.parameters())
        batch_predicted_tokens = phi(image_features.to(device=phi_parameter.device, dtype=phi_parameter.dtype))
        predicted_tokens.append(batch_predicted_tokens.cpu())
        names_list.extend(names)

    if not predicted_tokens:
        raise ValueError("Dataset contains no usable images")
    predicted_tokens = torch.vstack(predicted_tokens)
    return predicted_tokens, names_list


@torch.no_grad()
def extract_image_features_with_names(clip_model: CLIPVisionModelWithProjection, dataset: Dataset) -> Tuple[torch.Tensor, List[str]]:
    """
    Extracts image features from a dataset using a CLIP model
    """
    data_loader = DataLoader(dataset=dataset, batch_size=32, num_workers=10, pin_memory=False,
                             collate_fn=collate_fn)
    predicted_tokens = []
    names_list = []
    print(f"Extracting tokens using phi model")
    for batch in tqdm(data_loader):
        if batch is None:
            continue
        images = batch.get('image')
        names = batch.get('image_name')
        if images is None:
            images = batch.get('reference_image')
        if names is None:
            names = batch.get('reference_name')

        images = images.to(clip_model.device)
        image_features = clip_model(pixel_values=images.to(clip_model.dtype)).image_embeds

        #batch_predicted_tokens = phi(image_features)
        batch_predicted_tokens = image_features
        predicted_tokens.append(batch_predicted_tokens.cpu())
        names_list.extend(names)

    if not predicted_tokens:
        raise ValueError("Dataset contains no usable images")
    predicted_tokens = torch.vstack(predicted_tokens)
    return predicted_tokens, names_list

class CustomTensorDataset(Dataset):
    """
    Custom Tensor Dataset which yields image_features and image_names
    """

    def __init__(self, images: torch.Tensor, names: torch.Tensor):
        if len(images) != len(names):
            raise ValueError("Image features and names must have matching lengths")
        self.images = images
        self.names = names

    def __getitem__(self, index) -> dict:
        return {'image': self.images[index],
                'image_name': self.names[index]
                }

    def __len__(self):
        return len(self.images)


def get_templates():
    """
    Return a list of templates
    Same templates as in PALAVRA: https://arxiv.org/abs/2204.01694
    """
    return [
        "This is a photo of a {}",
        "This photo contains a {}",
        "A photo of a {}",
        "This is an illustration of a {}",
        "This illustration contains a {}",
        "An illustrations of a {}",
        "This is a sketch of a {}",
        "This sketch contains a {}",
        "A sketch of a {}",
        "This is a diagram of a {}",
        "This diagram contains a {}",
        "A diagram of a {}",
        "A {}",
        "We see a {}",
        "{}",
        "We see a {} in this photo",
        "We see a {} in this image",
        "We see a {} in this illustration",
        "We see a {} photo",
        "We see a {} image",
        "We see a {} illustration",
        "{} photo",
        "{} image",
        "{} illustration",
    ]
