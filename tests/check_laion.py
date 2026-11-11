"""Offline checks for LAION sampling, ranking, and bounded HTTP Range reads."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# Cho phép chạy trực tiếp file này mà không cần `python -m`.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from lincir.core.laion_online import LaionIndex, MODEL, image_url
from lincir.core.runtime_config import ROOT
from lincir.data.prepare_laion import RangeFile, prepare


class LaionChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'index'

    def fixture(self):
        self.folder.mkdir()
        vectors = np.zeros((3, 768), dtype=np.float32)
        vectors[0, 0] = vectors[1, 1] = vectors[2, 2] = 1
        np.save(self.folder / 'vectors.npy', vectors)
        records = [{'id': i, 'url': f'https://example.com/{i}.jpg'} for i in range(3)]
        (self.folder / 'records.json').write_text(json.dumps(records), 'utf-8')
        (self.folder / 'manifest.json').write_text(json.dumps({'version': 1, 'model': MODEL, 'rows': 3}), 'utf-8')
        return vectors

    def test_vector_ranking_and_reject_invalid_queries(self):
        vectors = self.fixture()
        index = LaionIndex(self.folder)
        self.assertEqual(index.query(vectors[1] * 7, 1)[0]['id'], 1)
        self.assertAlmostEqual(index.query(vectors[1], 1)[0]['similarity'], 1)
        for query in ([0] * 768, [float('nan')] * 768, [1] * 512):
            with self.assertRaises(ValueError):
                index.query(query)

    def test_reject_wrong_backbone_and_corrupt_vectors(self):
        self.fixture()
        path = self.folder / 'manifest.json'
        manifest = json.loads(path.read_text('utf-8'))
        manifest['model'] = 'ViT-H-14'
        path.write_text(json.dumps(manifest), 'utf-8')
        with self.assertRaises(ValueError):
            LaionIndex(self.folder)
        manifest['model'] = MODEL
        path.write_text(json.dumps(manifest), 'utf-8')
        np.save(self.folder / 'vectors.npy', np.full((3, 768), np.nan, dtype=np.float32))
        with self.assertRaises(ValueError):
            LaionIndex(self.folder)

    def test_sample_preserves_url_vector_alignment_and_reuses_index(self):
        # A user-created empty output folder must not be mistaken for an index.
        self.folder.mkdir()
        vectors = np.eye(4, 768, dtype=np.float32)
        table = pa.table({'id': [10, 11, 12, 13],
                          'url': ['https://example.com/a.jpg', 'https://example.com/b.jpg',
                                  'javascript:bad', 'https://example.com/d.jpg'],
                          'caption': ['a', 'b', 'c', 'd'], 'NSFW': ['UNLIKELY', 'LIKELY', 'UNLIKELY', 'UNLIKELY'],
                          'vector': vectors.tolist()})
        content = io.BytesIO()
        pq.write_table(table, content)

        class Source(io.BytesIO):
            etag = 'fixture'
            transferred = len(content.getvalue())

        with patch('lincir.data.prepare_laion.RangeFile', return_value=Source(content.getvalue())) as remote:
            manifest = prepare(self.folder, rows=4)
            self.assertEqual(manifest['rows'], 2)
            if os.name == 'nt':
                permissions = subprocess.run(
                    ['powershell', '-NoProfile', '-NonInteractive', '-Command',
                     'Import-Module "$PSHOME/Modules/Microsoft.PowerShell.Security/Microsoft.PowerShell.Security.psd1"; '
                     '(Get-Acl -LiteralPath $env:LAION_TEST_INDEX).AreAccessRulesProtected'],
                    env={**os.environ, 'LAION_TEST_INDEX': str(self.folder)},
                    capture_output=True, text=True, check=True)
                self.assertEqual(permissions.stdout.strip(), 'False',
                                 'Published indexes must inherit the project ACL on Windows')
            index = LaionIndex(self.folder)
            self.assertEqual(index.query(vectors[3], 1)[0]['id'], 13)
            del index
            prepare(self.folder, rows=4)
            self.assertEqual(remote.call_count, 1)

    def test_missing_index_file_reports_the_actual_cause(self):
        self.fixture()
        (self.folder / 'records.json').unlink()
        with self.assertRaisesRegex(ValueError, 'records.json') as caught:
            LaionIndex(self.folder)
        self.assertIsInstance(caught.exception.__cause__, FileNotFoundError)

    def test_partial_index_is_preserved_without_downloading(self):
        self.folder.mkdir()
        path = self.folder / 'manifest.json'
        path.write_text('{}', 'utf-8')
        with patch('lincir.data.prepare_laion.RangeFile') as remote:
            with self.assertRaisesRegex(ValueError, 'records.json'):
                prepare(self.folder)
            remote.assert_not_called()
        self.assertEqual(path.read_text('utf-8'), '{}')

    def test_cli_error_supports_vietnamese_on_windows(self):
        result = subprocess.run(
            [sys.executable, '-B', '-m', 'lincir.data.prepare_laion', '--rows', '0'],
            cwd=ROOT, env={**os.environ, 'PYTHONIOENCODING': 'cp1252'}, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Không chuẩn bị được LAION', result.stdout.decode('utf-8'))
        self.assertNotIn(b'Traceback', result.stderr)

    def test_bad_remote_source_leaves_no_partial_index(self):
        with patch('lincir.data.prepare_laion.RangeFile', return_value=io.BytesIO(b'bad parquet')):
            with self.assertRaises((OSError, ValueError)):
                prepare(self.folder, rows=2)
        self.assertFalse(self.folder.exists())
        self.assertEqual(list(self.folder.parent.iterdir()), [])

    def test_url_validation(self):
        for url in ('javascript:alert(1)', 'https://user:password@example.com/a',
                    'https://example.com/a>\nscript', 'https://[broken', None):
            self.assertFalse(image_url(url))
        self.assertTrue(image_url('https://example.com/photo.jpg?q=1&v=2'))

    def test_range_checks_and_transfer_budget(self):
        class Response:
            status_code = 200
            headers = {'Content-Length': '10', 'ETag': 'test'}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def raise_for_status(self): pass
            def iter_content(self, *args): return iter([b'01234'])

        with patch('lincir.data.prepare_laion.requests.Session') as session:
            session.return_value.head.return_value = Response()
            session.return_value.get.return_value = Response()
            with RangeFile('https://example.com/file', max_bytes=5) as remote:
                with self.assertRaises(ValueError):
                    remote.read(6)
                session.return_value.get.assert_not_called()
                with self.assertRaisesRegex(ValueError, 'HTTP Range'):
                    remote.read(5)
                response = Response()
                response.status_code = 206
                response.headers = {'Content-Range': 'bytes 0-4/10'}
                session.return_value.get.return_value = response
                self.assertEqual(remote.read(5), b'01234')
                self.assertEqual(remote.tell(), 5)
                with self.assertRaises(ValueError):
                    remote.read(1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
