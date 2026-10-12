"""Download official CIRCO and COCO without storing the 20 GB archive locally."""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import time
import zipfile
import zlib

ROOT = Path(__file__).resolve().parent
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

COCO = 'https://s3.amazonaws.com/images.cocodataset.org/'
CIRCO = 'https://raw.githubusercontent.com/miccunifi/CIRCO/main/'


def session():
    client = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    client.mount('https://', HTTPAdapter(max_retries=retry))
    return client


def atomic_bytes(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.part', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(data)
        # Windows readers/scanners can briefly hold a file without delete sharing.
        # Retry the atomic replacement; never delete or truncate the saved target.
        for attempt in range(12):
            try:
                os.replace(temporary, path)
                break
            except OSError as error:
                if getattr(error, 'winerror', None) not in (5, 32, 33) or attempt == 11:
                    raise
                time.sleep(min(.05 * (2 ** attempt), .5))
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class RangeReader(io.RawIOBase):
    """Seekable HTTPS ZIP reader with one bounded block in RAM."""
    def __init__(self, client, url, block_size=8 * 1024 * 1024):
        self.client, self.url, self.block_size = client, url, block_size
        self.position, self.block_start, self.block = 0, -1, b''
        response = client.get(url, headers={'Range': 'bytes=0-0', 'Accept-Encoding': 'identity'}, timeout=60, stream=True)
        try:
            response.raise_for_status()
            if response.status_code != 206 or not response.headers.get('Content-Range', '').startswith('bytes 0-0/'):
                raise RuntimeError('Server does not support validated byte ranges')
            self.size = int(response.headers['Content-Range'].split('/')[-1])
        finally:
            response.close()

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if whence not in (0, 1, 2) or position < 0:
            raise ValueError('Invalid seek')
        self.position = position
        return position

    def read(self, size=-1):
        end = self.size if size < 0 else min(self.size, self.position + size)
        pieces = []
        while self.position < end:
            start = self.position // self.block_size * self.block_size
            if start != self.block_start:
                stop = min(start + self.block_size, self.size) - 1
                response = self.client.get(self.url, headers={'Range': f'bytes={start}-{stop}',
                    'Accept-Encoding': 'identity'}, timeout=120, stream=True)
                try:
                    response.raise_for_status()
                    expected = f'bytes {start}-{stop}/{self.size}'
                    if response.status_code != 206 or response.headers.get('Content-Range') != expected:
                        raise RuntimeError('Invalid range response; refusing corrupted archive')
                    block = response.raw.read(stop - start + 2)
                    if len(block) != stop - start + 1:
                        raise RuntimeError('Incomplete range response')
                finally:
                    response.close()
                self.block_start, self.block = start, block
            offset = self.position - start
            length = min(end - self.position, len(self.block) - offset)
            pieces.append(self.block[offset:offset + length])
            self.position += length
        return b''.join(pieces)


def validate_dataset(dataset, verify_images=False):
    info = json.loads((dataset / 'COCO2017_unlabeled/annotations/image_info_unlabeled2017.json').read_text('utf-8'))
    rows = json.loads((dataset / 'annotations/val.json').read_text('utf-8'))
    images = info['images']
    ids = {int(row['id']) for row in images}
    if len(ids) != len(images) or len(images) != 123403 or len(rows) != 220:
        raise ValueError('Unexpected official gallery/validation size or duplicate IDs')
    if len({int(row['id']) for row in rows}) != len(rows):
        raise ValueError('Duplicate query IDs')
    for row in rows:
        targets = set(map(int, row['gt_img_ids']))
        if not targets or int(row['target_img_id']) not in targets or not targets.issubset(ids):
            raise ValueError('Invalid ground truth IDs')
        if int(row['reference_img_id']) not in ids or int(row['reference_img_id']) in targets:
            raise ValueError('Invalid reference ID')
        if not isinstance(row['relative_caption'], str) or not row['relative_caption'].strip():
            raise ValueError('Empty relative caption')
    folder = (dataset / 'COCO2017_unlabeled/unlabeled2017').resolve()
    missing = []
    for row in images:
        path = (folder / row['file_name']).resolve()
        if not path.is_relative_to(folder):
            raise ValueError('Image path outside dataset')
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(row['file_name'])
        elif verify_images:
            from PIL import Image
            with Image.open(path) as image:
                image.verify()
    return {'gallery_count': len(images), 'validation_queries': len(rows),
            'present_images': len(images) - len(missing), 'missing_images': len(missing),
            'missing_examples': missing[:5], 'ready': not missing}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'benchmarks/CIRCO')
    parser.add_argument('--metadata-only', action='store_true')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--verify-images', action='store_true')
    args = parser.parse_args()
    dataset = args.dataset.resolve()
    if args.check:
        result = validate_dataset(dataset, args.verify_images)
        print(json.dumps(result, indent=2), flush=True)
        return 0 if result['ready'] else 2
    dataset.mkdir(parents=True, exist_ok=True)
    with session() as client:
        for name in ('annotations/val.json', 'annotations/test.json', 'LICENSE', 'README.md'):
            response = client.get(CIRCO + name, timeout=60)
            response.raise_for_status()
            content = response.content
            if name.endswith('.json'):
                json.loads(content)
            atomic_bytes(dataset / name, content)
        response = client.get(COCO + 'annotations/image_info_unlabeled2017.zip', timeout=120)
        response.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            member = 'annotations/image_info_unlabeled2017.json'
            atomic_bytes(dataset / 'COCO2017_unlabeled' / member, archive.read(member))
        print('Official metadata downloaded.', flush=True)
        if args.metadata_only:
            print(json.dumps(validate_dataset(dataset), indent=2), flush=True)
            return 0
        folder = dataset / 'COCO2017_unlabeled'
        folder.mkdir(exist_ok=True)
        with RangeReader(client, COCO + 'zips/unlabeled2017.zip') as remote, zipfile.ZipFile(remote) as archive:
            members = [m for m in archive.infolist() if not m.is_dir()]
            needed = 0
            for member in members:
                target = (folder / member.filename).resolve()
                if not target.is_relative_to(folder.resolve()) or not member.filename.startswith('unlabeled2017/'):
                    raise ValueError('Unsafe ZIP member')
                if not target.is_file() or target.stat().st_size != member.file_size:
                    needed += member.file_size
            free = shutil.disk_usage(folder).free
            print(f'Images: {len(members)}; missing bytes: {needed}; free bytes: {free}', flush=True)
            if needed + 1024**3 > free:
                raise OSError('Not enough disk space including 1 GiB reserve; use --dataset on a larger drive')
            downloaded = 0
            started = time.monotonic()
            for number, member in enumerate(members, 1):
                target = folder / member.filename
                existing = target.read_bytes() if target.is_file() and target.stat().st_size == member.file_size else None
                if existing is None or zlib.crc32(existing) != member.CRC:
                    data = archive.read(member)  # ZIP CRC checked before atomic replacement.
                    atomic_bytes(target, data)
                    downloaded += len(data)
                if number % 1000 == 0 or number == len(members):
                    status = {'phase': 'images', 'processed': number, 'total': len(members),
                              'downloaded_image_bytes_this_run': downloaded,
                              'elapsed_seconds': round(time.monotonic() - started, 1)}
                    atomic_bytes(dataset / 'download_status.json', json.dumps(status).encode())
                    print(json.dumps(status), flush=True)
        result = validate_dataset(dataset)
        atomic_bytes(dataset / 'download_status.json', json.dumps(result, indent=2).encode())
        print(json.dumps(result, indent=2), flush=True)
        return 0 if result['ready'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
