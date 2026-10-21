"""Search cached LAION CLIP vectors; return remote image URLs, never image files."""
import json
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np

DEFAULT_INDEX = Path(__file__).resolve().parent / 'outputs/laion_index'
MODEL = 'openai/clip-vit-large-patch14'


def image_url(value):
    if not isinstance(value, str) or any(c in value for c in '<>\r\n\\'):
        return False
    try:
        url = urlsplit(value)
        return (url.scheme in ('https', 'http') and bool(url.hostname)
                and url.username is None and url.password is None)
    except ValueError:
        return False


class LaionIndex:
    def __init__(self, folder=DEFAULT_INDEX):
        folder = Path(folder)
        try:
            self.manifest = json.loads((folder / 'manifest.json').read_text('utf-8'))
            self.records = json.loads((folder / 'records.json').read_text('utf-8'))
            self.vectors = np.load(folder / 'vectors.npy', mmap_mode='r', allow_pickle=False)
        except (OSError, ValueError) as error:
            raise ValueError(f'Không đọc được chỉ mục LAION tại {folder}: {error}') from error
        if (not isinstance(self.manifest, dict) or not isinstance(self.records, list)
                or self.manifest.get('version') != 1 or self.manifest.get('model') != MODEL
                or self.vectors.dtype != np.float32 or self.vectors.ndim != 2
                or self.vectors.shape != (len(self.records), 768)
                or not self.records or self.manifest.get('rows') != len(self.records)
                or any(not isinstance(row, dict) or not image_url(row.get('url')) for row in self.records)):
            raise ValueError('Chỉ mục LAION không tương thích với CLIP ViT-L/14 của LinCIR.')
        # Validate in batches so a corrupt cache cannot produce plausible results.
        for start in range(0, len(self.records), 4096):
            block = self.vectors[start:start + 4096]
            if not np.isfinite(block).all() or not np.allclose(np.linalg.norm(block, axis=1), 1, atol=.001):
                raise ValueError('Vector LAION bị hỏng hoặc chưa chuẩn hóa. Hãy tạo lại chỉ mục.')

    def query(self, embedding_input, num_images=6):
        query = np.asarray(embedding_input, dtype=np.float32)
        norm = np.linalg.norm(query.astype(np.float64))
        if query.shape != (768,) or not np.isfinite(query).all() or not np.isfinite(norm) or norm <= 0:
            raise ValueError('Truy vấn phải là vector CLIP ViT-L/14 gồm 768 giá trị hữu hạn.')
        if not isinstance(num_images, int) or not 1 <= num_images <= 100:
            raise ValueError('Số kết quả phải nằm trong khoảng 1–100.')
        query = (query / norm).astype(np.float32)
        scores = self.vectors @ query
        order = np.argsort(-scores, kind='stable')
        results, seen = [], set()
        for position in order:
            row = self.records[int(position)]
            if row['url'] in seen:
                continue
            seen.add(row['url'])
            results.append({**row, 'similarity': float(scores[position])})
            if len(results) == num_images:
                break
        return results
