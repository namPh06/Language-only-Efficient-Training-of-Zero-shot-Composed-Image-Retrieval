"""Prepare a bounded sample of LAION vectors and URLs, without downloading images."""
import argparse
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time
from uuid import uuid4

import numpy as np
import requests

# Cho phép chạy trực tiếp file này mà không cần `python -m`.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from lincir.core.laion_online import DEFAULT_INDEX, MODEL, LaionIndex, image_url

DATASET_URL = 'https://clickhouse-datasets.s3.amazonaws.com/laion-5b/laion5b_100m_part_1_of_10.parquet'


class RangeFile(io.RawIOBase):
    """Read only requested Parquet byte ranges, bounded by a transfer budget."""
    def __init__(self, url, max_bytes=512 * 1024 * 1024):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'LinCIR-LAION-index/1.0', 'Accept-Encoding': 'identity'})
        self.url, self.max_bytes = url, max_bytes
        self.position = self.transferred = 0
        try:
            with self.session.head(url, timeout=(10, 30)) as response:
                response.raise_for_status()
                self.size = int(response.headers['Content-Length'])
                self.etag = response.headers.get('ETag')
        except BaseException:
            self.session.close()
            raise

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        if whence not in (0, 1, 2):
            raise ValueError('Invalid seek origin')
        position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        if not 0 <= position <= self.size:
            raise ValueError('Invalid remote file offset')
        self.position = position
        return position

    def read(self, size=-1):
        size = self.size - self.position if size < 0 else min(size, self.size - self.position)
        if not size:
            return b''
        if self.transferred + size > self.max_bytes:
            raise ValueError('Vượt ngân sách tải metadata/vector. Giảm --rows hoặc tăng --max-download-mib.')
        start = self.position
        headers = {'Range': f'bytes={start}-{start + size - 1}'}
        if self.etag:
            headers['If-Match'] = self.etag
        with self.session.get(self.url, headers=headers, stream=True, timeout=(10, 45)) as response:
            response.raise_for_status()
            expected = f'bytes {start}-{start + size - 1}/{self.size}'
            if response.status_code != 206 or response.headers.get('Content-Range') != expected:
                raise ValueError('Nguồn dữ liệu không trả đúng HTTP Range; dừng để tránh tải toàn bộ file.')
            buffer = io.BytesIO()
            announced = time.monotonic()
            for chunk in response.iter_content(1024 * 1024):
                self.transferred += len(chunk)
                if buffer.tell() + len(chunk) > size or self.transferred > self.max_bytes:
                    raise ValueError('Nguồn trả vượt giới hạn dữ liệu cho phép.')
                buffer.write(chunk)
                if time.monotonic() - announced >= 5:
                    print(f'Đã nhận {self.transferred / 1024**2:.1f} MiB metadata/vector...', flush=True)
                    announced = time.monotonic()
            if buffer.tell() != size:
                raise OSError('Kết nối bị ngắt trước khi nhận đủ dữ liệu.')
        self.position += size
        return buffer.getvalue()

    def close(self):
        self.session.close()
        super().close()


def prepare(folder=DEFAULT_INDEX, rows=50000, row_group=0, max_download_mib=512):
    try:
        import pyarrow.parquet as pq
    except ImportError as error:
        raise ValueError('Cài bộ đọc dữ liệu: python -m pip install -r requirements/requirements-online.txt') from error
    if not 1 <= rows <= 200000 or row_group < 0 or max_download_mib <= 0:
        raise ValueError('rows: 1–200000; row-group: >= 0; ngân sách tải: > 0 MiB.')
    folder = Path(folder).resolve()
    # A new folder avoids replacing a working index while a demo is using its mmap.
    if folder.is_dir() and not any(folder.iterdir()):
        folder.rmdir()
    if folder.exists():
        index = LaionIndex(folder)
        if index.manifest['requested_rows'] != rows or index.manifest['row_group'] != row_group:
            raise ValueError('Thư mục đã có chỉ mục khác. Chọn --output mới để tạo mẫu khác.')
        print(f'Đã có {len(index.records):,} vector LAION tại {folder}; không tải lại.', flush=True)
        return index.manifest
    folder.parent.mkdir(parents=True, exist_ok=True)
    # Inherit project permissions: mkdtemp's private Windows ACL survives renaming.
    staging = folder.parent / f'.laion-{uuid4().hex}'
    staging.mkdir()
    try:
        records = []
        scanned = 0
        vectors = np.lib.format.open_memmap(staging / 'vectors.npy', mode='w+', dtype='float32', shape=(rows, 768))
        with RangeFile(DATASET_URL, max_download_mib * 1024**2) as remote:
            parquet = pq.ParquetFile(remote, pre_buffer=False, buffer_size=1024 * 1024)
            if row_group >= parquet.num_row_groups:
                raise ValueError(f'Chỉ có {parquet.num_row_groups} row group; chọn từ 0.')
            group_rows = parquet.metadata.row_group(row_group).num_rows
            print(f'Đọc tối đa {min(rows, group_rows):,} dòng LAION; chỉ giữ vector và URL, không tải ảnh.', flush=True)
            # shortcut: one row group per index keeps setup bounded; use a server for a full corpus.
            for batch in parquet.iter_batches(batch_size=2048, row_groups=[row_group],
                                              columns=['id', 'url', 'caption', 'NSFW', 'vector'], use_threads=False):
                batch = batch.slice(0, min(len(batch), rows - scanned))
                scanned += len(batch)
                data = batch.to_pydict()
                for i, vector in enumerate(data['vector']):
                    if data['NSFW'][i] != 'UNLIKELY' or not image_url(data['url'][i]):
                        continue
                    value = np.asarray(vector, dtype=np.float32)
                    if value.shape != (768,) or not np.isfinite(value).all():
                        continue
                    norm = np.linalg.norm(value)
                    if norm <= 0:
                        continue
                    vectors[len(records)] = value / norm
                    records.append({'id': data['id'][i], 'url': data['url'][i], 'caption': data['caption'][i]})
                if scanned >= rows:
                    break
            manifest = {'version': 1, 'model': MODEL, 'dataset_url': DATASET_URL,
                        'source_etag': remote.etag, 'requested_rows': rows, 'scanned_rows': scanned,
                        'row_group': row_group, 'rows': len(records), 'downloaded_bytes': remote.transferred,
                        'created_at': time.strftime('%Y-%m-%dT%H:%M:%S%z')}
        if not records:
            raise ValueError('Không có vector hợp lệ trong mẫu LAION.')
        # Write only accepted rows; the temporary capacity file is not a valid index.
        vectors.flush()
        np.save(staging / 'accepted.npy', vectors[:len(records)], allow_pickle=False)
        del vectors
        os.replace(staging / 'accepted.npy', staging / 'vectors.npy')
        (staging / 'records.json').write_text(json.dumps(records, ensure_ascii=False), 'utf-8')
        (staging / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), 'utf-8')
        LaionIndex(staging)
        staging.rename(folder)
        print(f'Sẵn sàng: {len(records):,} URL/vector LAION tại {folder}. Không có file ảnh nào được tải.', flush=True)
        return manifest
    finally:
        # Close mmap handles before cleanup, including on failed downloads on Windows.
        if 'vectors' in locals():
            del vectors
        if staging.exists():
            shutil.rmtree(staging)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_INDEX)
    parser.add_argument('--rows', type=int, default=50000, help='Số dòng tối đa trong mẫu, mặc định 50000.')
    parser.add_argument('--row-group', type=int, default=0)
    parser.add_argument('--max-download-mib', type=int, default=512)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        if args.check:
            index = LaionIndex(args.output)
            print(json.dumps(index.manifest, ensure_ascii=False, indent=2))
        else:
            prepare(args.output, args.rows, args.row_group, args.max_download_mib)
    except (OSError, ValueError, requests.RequestException) as error:
        print(f'Không chuẩn bị được LAION: {error}')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
