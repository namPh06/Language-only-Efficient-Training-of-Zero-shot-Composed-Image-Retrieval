"""Run the published LinCIR checkpoint on a photo, without training or downloads."""
from runtime_config import DEFAULT_MODEL_CACHE, CLIP_REVISION, TOKENIZER_REVISION
import argparse
import hashlib
import json
import sys
from pathlib import Path
import time

import torch
from PIL import Image, ImageOps
from transformers import CLIPTokenizer, CLIPTextModelWithProjection, CLIPVisionModelWithProjection
try:
    from transformers import CLIPImageProcessorPil as CLIPImageProcessor
except ImportError:
    from transformers import CLIPImageProcessor
from models import Phi
from encode_with_pseudo_tokens import encode_with_pseudo_tokens_HF


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parent
    parser.add_argument('--image', default=str(root / 'example1.jpg'))
    parser.add_argument('--text', default='is a pencil sketch')
    parser.add_argument('--cache', default=DEFAULT_MODEL_CACHE)
    parser.add_argument('--device', default='cpu', choices=['cpu', 'cuda'])
    args = parser.parse_args()
    if not args.text.strip() or args.text.count('$') > 1:
        parser.error('Mô tả không được rỗng và chỉ được chứa tối đa một ký hiệu $.')
    if not Path(args.image).is_file():
        parser.error('Ảnh tham chiếu không tồn tại. Kiểm tra --image.')
    torch.set_num_threads(4)
    checkpoint = root / 'pretrained_models/lincir_large.pt'
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    if digest != '5ba98d52db7a5e9a78f9ba7436991235477b89544caf246e4659642bf9b409bd':
        raise ValueError('Published checkpoint checksum does not match.')
    if args.device == 'cuda' and not torch.cuda.is_available():
        raise RuntimeError('CUDA is unavailable in this Python environment.')
    device = torch.device(args.device)
    start = time.perf_counter()
    backbone = 'openai/clip-vit-large-patch14'
    options = dict(cache_dir=args.cache, local_files_only=True, revision=CLIP_REVISION)
    print('Loading cached CLIP and published Phi...', flush=True)
    vision = CLIPVisionModelWithProjection.from_pretrained(backbone, **options).to(device).eval()
    encoder = CLIPTextModelWithProjection.from_pretrained(backbone, **options).to(device).eval()
    tokenizer = CLIPTokenizer.from_pretrained(
        'stabilityai/stable-diffusion-xl-base-1.0', subfolder='tokenizer_2', **{**options, 'revision': TOKENIZER_REVISION})
    if tokenizer.encode('$', add_special_tokens=False) != [259]:
        raise ValueError('Tokenizer does not match the published pseudo-token ID.')
    phi = Phi(encoder.config.projection_dim, encoder.config.projection_dim * 4,
              encoder.config.hidden_size, 0.5).to(device).eval()
    state = torch.load(checkpoint, map_location='cpu', weights_only=True)
    phi.load_state_dict(state['Phi'])
    processor = CLIPImageProcessor(
        crop_size={'height': 224, 'width': 224}, size={'shortest_edge': 224},
        do_center_crop=True, do_convert_rgb=True, do_normalize=True,
        do_rescale=True, do_resize=True, resample=3,
        image_mean=[0.48145466, 0.4578275, 0.40821073],
        image_std=[0.26862954, 0.26130258, 0.27577711])
    with Image.open(args.image) as image:
        pixels = processor(images=ImageOps.exif_transpose(image).convert('RGB'), return_tensors='pt').pixel_values.to(device)
    prompt = args.text.strip()
    if '$' not in prompt:
        prompt = 'a photo of $ that ' + prompt
    prompt = prompt.replace('$', ' $ ')
    if len(tokenizer(prompt, truncation=False).input_ids) > 77:
        parser.error('Mô tả vượt giới hạn 77 token của CLIP; hãy viết ngắn hơn.')
    tokens = tokenizer(prompt, padding='max_length', truncation=True,
                       max_length=77, return_tensors='pt').input_ids.to(device)
    if tokens.eq(259).sum().item() != 1:
        raise ValueError('Prompt lost its pseudo-token.')
    with torch.inference_mode():
        features = vision(pixel_values=pixels).image_embeds
        pseudo = phi(features)
        composed = encode_with_pseudo_tokens_HF(encoder, tokens, pseudo)
    if composed.shape != (1, 768) or not torch.isfinite(composed).all():
        raise RuntimeError('Invalid composed embedding.')
    report = dict(status='PASS', device=str(device), image=str(Path(args.image).resolve()),
                  prompt=prompt, checkpoint_sha256=digest,
                  image_shape=list(features.shape), pseudo_shape=list(pseudo.shape),
                  composed_shape=list(composed.shape), elapsed_seconds=time.perf_counter()-start,
                  note='Published checkpoint inference; no training or CIRR benchmark.')
    output = root / 'outputs/pretrained_run.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
