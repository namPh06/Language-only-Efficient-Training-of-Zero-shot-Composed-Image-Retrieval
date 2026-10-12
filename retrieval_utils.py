"""Shared exact ranking and legacy raw-reference cache identity; no retrieval mode."""
from pathlib import Path
import hashlib,json,torch
VERSION='fast-evidence-v1'
def exact_topk(scores, eligible, count):
    """Match stable descending argsort, including ties at the K boundary."""
    if scores.ndim != 1 or not torch.isfinite(scores).all():
        raise ValueError('Invalid score vector')
    ids = torch.as_tensor(eligible, dtype=torch.long, device=scores.device)
    count = min(int(count), len(ids))
    if count <= 0:
        return []
    values = scores[ids]
    boundary = torch.topk(values, count, sorted=False).values.min()
    # Keep all tied candidates until stable ordering resolves the boundary.
    retained = torch.nonzero(values >= boundary, as_tuple=False).flatten()
    order = torch.argsort(values[retained], descending=True, stable=True)[:count]
    return ids[retained[order]].cpu().tolist()


class ReferenceCacheIdentity:
    def __init__(self, encoder, tokenizer, model_cache):
        import transformers
        files = []
        folder = Path(model_cache) / 'models--openai--clip-vit-large-patch14'
        for path in sorted(folder.rglob('*')) if folder.exists() else []:
            if path.is_file() and path.suffix in ('.safetensors', '.bin', '.json'):
                stat = path.stat()
                files.append((str(path.resolve()), stat.st_size, stat.st_mtime_ns))
        payload = [VERSION, transformers.__version__, encoder.config.to_dict(),
                   sorted(tokenizer.get_vocab().items()), files,
                   '88de78fa3b216ec22af1c604f48bdc8afb6287866b31e232a43926e1c67387c9']
        key = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
        self.warning = ''
        self.key = key
