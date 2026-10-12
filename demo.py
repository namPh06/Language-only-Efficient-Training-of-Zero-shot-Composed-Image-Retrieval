"""LinCIR local gallery demo: published weights, no training required.

LinCIR model and pseudo-token encoder: NAVER Corp., CC BY-NC-4.0.
"""
from runtime_config import DEFAULT_MODEL_CACHE, CLIP_REVISION, TOKENIZER_REVISION
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import argparse
import hashlib
import threading
import time
import math
import tempfile
import pickle
from io import BytesIO
from collections import OrderedDict
from functools import wraps
from urllib.parse import urlparse
import requests
os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')
import gradio as gr
import torch
import torch.nn.functional as F
from PIL import Image, ImageOps
from transformers import CLIPTokenizer, CLIPTextModelWithProjection, CLIPVisionModelWithProjection
try:
    from transformers import CLIPImageProcessorPil as CLIPImageProcessor
except ImportError:
    from transformers import CLIPImageProcessor
from models import Phi
from encode_with_pseudo_tokens import encode_with_pseudo_tokens_HF
from retrieval_utils import ReferenceCacheIdentity, exact_topk
from upgraded_retrieval import MODE as UPGRADED_MODE, bounded_gate, is_negative, adaptive_prompt
EXTENSIONS = {'.jpg','.jpeg','.png','.webp','.bmp','.tif','.tiff'}


def read_image(path):
    with Image.open(path) as source:
        return ImageOps.exif_transpose(source).convert('RGB')


def image_digest(image):
    return hashlib.sha256(str(image.size).encode() + image.tobytes()).hexdigest()


def file_stamp(path):
    try:
        stat = Path(path).stat()
        return stat.st_size, stat.st_mtime_ns
    except (OSError, TypeError, ValueError):
        return None


def serialized_search(method):
    """Keep comparisons on one gallery snapshot, including nested searches."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)
    return wrapped


class LocalRetriever:
    def __init__(self, gallery, cache=DEFAULT_MODEL_CACHE, device='cpu', source='local',
                 result_limit=20, exclude_reference_by_id=False, write_search_artifacts=True):
        if result_limit not in (20, 50):
            raise ValueError('result_limit must be 20 (demo) or 50 (benchmark)')
        self.result_limit = result_limit
        self.exclude_reference_by_id = exclude_reference_by_id
        self.write_search_artifacts = write_search_artifacts
        self.source = source
        self.gallery = Path(gallery).resolve()
        self.gallery.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.signature = None
        self.paths, self.digests, self.skipped = [], [], []
        self.index_records = {}
        self.index_cache_path = ROOT / 'outputs/index' / (hashlib.sha256(str(self.gallery).encode()).hexdigest()[:24]+'.pt')
        self.index_cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_cache_loaded = False
        self.reference_cache = OrderedDict()
        self.query_cache = OrderedDict()
        torch.set_num_threads(1)
        if device == 'auto':
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        if device == 'cuda' and not torch.cuda.is_available():
            raise RuntimeError('Python hiện tại chưa hỗ trợ CUDA. Dùng --device cpu.')
        self.device = torch.device(device)
        checkpoint = ROOT / 'pretrained_models/lincir_large.pt'
        if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != '5ba98d52db7a5e9a78f9ba7436991235477b89544caf246e4659642bf9b409bd':
            raise ValueError('Checkpoint LinCIR không khớp bản đã kiểm tra.')
        print('Đang nạp CLIP và LinCIR đã train sẵn...', flush=True)
        options = dict(cache_dir=cache, local_files_only=True, revision=CLIP_REVISION)
        backbone = 'openai/clip-vit-large-patch14'
        self.vision = CLIPVisionModelWithProjection.from_pretrained(backbone, **options).to(self.device).eval()
        self.encoder = CLIPTextModelWithProjection.from_pretrained(backbone, **options).to(self.device).eval()
        self.tokenizer = CLIPTokenizer.from_pretrained('stabilityai/stable-diffusion-xl-base-1.0', subfolder='tokenizer_2', **{**options, 'revision': TOKENIZER_REVISION})
        if self.tokenizer.encode('$', add_special_tokens=False) != [259]:
            raise ValueError('Tokenizer không đúng với pseudo-token LinCIR.')
        self.phi = Phi(self.encoder.config.projection_dim, self.encoder.config.projection_dim * 4,
                       self.encoder.config.hidden_size, 0.5).to(self.device).eval()
        self.phi.load_state_dict(torch.load(checkpoint, map_location='cpu', weights_only=True)['Phi'])
        self.processor = CLIPImageProcessor(crop_size={'height': 224, 'width': 224}, size={'shortest_edge': 224},
            do_center_crop=True, do_convert_rgb=True, do_normalize=True, do_rescale=True, do_resize=True,
            resample=3, image_mean=[0.48145466, 0.4578275, 0.40821073], image_std=[0.26862954, 0.26130258, 0.27577711])
        self.fast_bank = None
        self.model_cache = cache


    def _features(self, images):
        pixels = self.processor(images=images, return_tensors='pt').pixel_values.to(self.device)
        return self.vision(pixel_values=pixels).image_embeds


    @torch.inference_mode()
    def _index(self):
        if not self.index_cache_loaded:
            self.index_cache_loaded = True
            try:
                stored = torch.load(self.index_cache_path, map_location='cpu', weights_only=True)
                if stored.get('version') == 'clip-large-pil224-index-v1' and stored.get('gallery') == str(self.gallery):
                    for key, digest, vector in stored['records']:
                        if (isinstance(key, (tuple, list)) and len(key) == 3
                                and isinstance(key[0], str) and isinstance(digest, str)
                                and len(digest) == 64 and isinstance(vector, torch.Tensor)
                                and vector.dtype == torch.float32 and vector.shape == (768,) and torch.isfinite(vector).all()
                                and abs(float(vector.norm())-1) < .01):
                            self.index_records[tuple(key)] = (digest, vector)
            except (OSError, RuntimeError, ValueError, TypeError, KeyError, AttributeError,
                    IndexError, EOFError, pickle.UnpicklingError):
                # A damaged/unavailable cache never prevents rebuilding the index.
                self.index_records = {}
        files, scan_errors = [], []
        for path in sorted(self.gallery.rglob('*')):
            if path.suffix.lower() not in EXTENSIONS:
                continue
            try:
                if path.is_file():
                    stat = path.stat()
                    files.append((path, (str(path), stat.st_size, stat.st_mtime_ns)))
            except OSError as error:
                scan_errors.append(f'{path.name}: {error}')
        signature = tuple(key for _, key in files)
        if signature == self.signature:
            return
        paths, keys, skipped, batch, pending = [], [], scan_errors, [], []
        records = {}

        def flush():
            if batch:
                vectors = F.normalize(self._features(batch), dim=-1).cpu()
                for (key, digest), vector in zip(pending, vectors):
                    records[key] = (digest, vector.clone())
                batch.clear()
                pending.clear()

        for path, key in files:
            if key in self.index_records:
                records[key] = self.index_records[key]
                paths.append(path)
                keys.append(key)
                continue
            try:
                image = read_image(path)
                digest = image_digest(image)
            except (OSError, ValueError) as error:
                skipped.append(f'{path.name}: {error}')
                continue
            paths.append(path)
            keys.append(key)
            batch.append(image)
            pending.append((key, digest))
            if len(batch) == 4:
                flush()
        flush()
        # Disk records stay on CPU; query vectors follow the selected device.
        # Keep the search matrix there too, otherwise --device cuda fails at
        # matrix multiplication even though loading the models succeeds.
        self.features = (torch.stack([records[key][1] for key in keys]).to(self.device)
                         if keys else torch.empty((0, 768), device=self.device))
        self.paths, self.digests, self.skipped = paths, [records[key][0] for key in keys], skipped
        self.index_records = records
        self.signature = signature
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.index_cache_path.parent, suffix='.tmp', delete=False) as handle:
                temporary = Path(handle.name)
            torch.save({'version': 'clip-large-pil224-index-v1', 'gallery': str(self.gallery),
                        'records': [(key, digest, vector) for key, (digest, vector) in records.items()]}, temporary)
            os.replace(temporary, self.index_cache_path)
        except (OSError, RuntimeError) as error:
            print(f'Không lưu được cache chỉ mục; tìm kiếm vẫn hoạt động: {error}', flush=True)
        finally:
            if temporary is not None:
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass  # A cleanup failure must not disable an in-memory index.


    def _candidate_indices(self, reference, digest):
        if self.exclude_reference_by_id:
            reference = Path(reference).resolve()
            return [i for i, path in enumerate(self.paths) if path != reference]
        return [i for i, value in enumerate(self.digests) if value != digest]


    def _reference_features(self, image, digest):
        if digest not in self.reference_cache:
            self.reference_cache[digest] = self._features([image])
            if len(self.reference_cache) > 16:
                self.reference_cache.popitem(last=False)
        self.reference_cache.move_to_end(digest)
        return self.reference_cache[digest]


    def _query_features(self, image, digest, tokens):
        # Preserve an exact padded-context fallback and separate its query cache.
        full_context = os.environ.get('LINCIR_FULL_TEXT_CONTEXT') == '1'
        key = (digest, tuple(tokens[0].detach().cpu().tolist()), full_context)
        if key not in self.query_cache:
            pseudo = self.phi(self._reference_features(image, digest))
            # CLIP pools at the first EOT; causal attention makes later padding irrelevant.
            end = tokens.shape[1] if full_context else int(tokens.argmax(dim=-1).max().item()) + 1
            self.query_cache[key] = F.normalize(encode_with_pseudo_tokens_HF(self.encoder, tokens[:, :end], pseudo), dim=-1).cpu()
            if len(self.query_cache) > 16:
                self.query_cache.popitem(last=False)
        self.query_cache.move_to_end(key)
        return self.query_cache[key].to(self.device)


    def add_images(self, files):
        if not files:
            raise gr.Error('Hãy chọn ảnh cần thêm vào kho trước.')
        with self.lock:
            count = 0
            failures = []
            if isinstance(files, (str, Path)):
                files = [files]
            for filename in files:
                temporary = None
                try:
                    source = Path(filename)
                    content = source.read_bytes()
                    image = read_image(BytesIO(content))
                    digest = hashlib.sha256(content).hexdigest()[:20]
                    suffix = source.suffix.lower() if source.suffix.lower() in EXTENSIONS else '.png'
                    destination = self.gallery / f'{digest}{suffix}'
                    if not destination.exists():
                        with tempfile.NamedTemporaryFile(dir=self.gallery, suffix='.tmp', delete=False) as handle:
                            temporary = Path(handle.name)
                            if source.suffix.lower() in EXTENSIONS:
                                handle.write(content)
                            else:
                                image.save(handle, format='PNG')
                        os.replace(temporary, destination)
                        count += 1
                except (OSError, ValueError, TypeError) as error:
                    failures.append(f'{filename}: {error}')
                finally:
                    if temporary is not None:
                        try:
                            temporary.unlink(missing_ok=True)
                        except OSError:
                            pass
            if count:
                self.signature = None
        if failures and not count:
            raise gr.Error('Không thêm được ảnh mới. ' + '; '.join(failures[:3]))
        message = f'Đã thêm {count} ảnh mới. Kho ảnh: {self.gallery}'
        if failures:
            message += f' Bỏ qua {len(failures)} file lỗi: ' + '; '.join(failures[:3])
        return message


    def _ensure_fast_bank(self):
        if self.fast_bank is None:
            self.fast_bank = ReferenceCacheIdentity(self.encoder, self.tokenizer, self.model_cache)
        return self.fast_bank


    @torch.inference_mode()
    def _fast_reference_features(self, image, digest):
        if digest in self.reference_cache:
            self.reference_cache.move_to_end(digest)
            return self.reference_cache[digest]
        bank = self._ensure_fast_bank()
        path = ROOT / 'outputs/fast_reference' / bank.key[:16] / (digest[:32] + '.pt')
        vector = None
        try:
            stored = torch.load(path, map_location='cpu', weights_only=True)
            vector = stored['vector'] if stored['encoder'] == bank.key and stored['digest'] == digest else None
            if (not isinstance(vector, torch.Tensor) or vector.shape != (1, 768)
                    or vector.dtype != torch.float32 or not torch.isfinite(vector).all() or float(vector.norm()) <= 0):
                vector = None
        except (OSError, RuntimeError, ValueError, TypeError, KeyError, EOFError, pickle.UnpicklingError):
            pass
        if vector is None:
            vector = self._reference_features(image, digest).detach().cpu().float()
            temporary = None
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.NamedTemporaryFile(dir=path.parent, suffix='.tmp', delete=False) as handle:
                    temporary = Path(handle.name)
                torch.save({'encoder':bank.key,'digest':digest,'vector':vector}, temporary)
                os.replace(temporary, path)
            except OSError:
                bank.warning = 'Không lưu được đặc trưng tham chiếu; tìm kiếm vẫn hoạt động.'
            finally:
                if temporary is not None:
                    try:
                        temporary.unlink(missing_ok=True)
                    except OSError:
                        pass
        self.reference_cache[digest] = vector.to(self.device)
        self.reference_cache.move_to_end(digest)
        while len(self.reference_cache) > 16:
            self.reference_cache.popitem(last=False)
        return self.reference_cache[digest]


    def search_upgraded(self, reference, description, top_k):
        if self.source != 'local':
            raise gr.Error('Chế độ kết hợp điểm hỗ trợ kho local.')
        return self.search(reference, description, top_k, upgraded=True)


    def search_laion(self, reference, tokens, top_k):
        from clip_client import ClipClient
        with self.lock, torch.inference_mode():
            try:
                image = read_image(reference)
            except (OSError, ValueError) as error:
                raise gr.Error('Không đọc được ảnh tham chiếu. Hãy chọn lại ảnh hợp lệ.') from error
            pseudo = self.phi(self._reference_features(image, image_digest(image)))
            query = F.normalize(encode_with_pseudo_tokens_HF(self.encoder, tokens, pseudo), dim=-1)
            if not torch.isfinite(query).all():
                raise gr.Error('Model trả về vector truy vấn không hợp lệ.')
            embedding = query[0].cpu().tolist()
        client = ClipClient(url='https://knn.laion.ai/knn-service',
                            indice_name='laion5B-L-14', num_images=int(top_k), timeout=20)
        try:
            results = client.query(embedding_input=embedding)
        except requests.RequestException as error:
            raise gr.Error('Không kết nối được LAION. Dịch vụ hoặc đường mạng hiện không sẵn sàng. '
                           'Thử lại sau hoặc chạy python demo.py để dùng kho local.') from error
        except ValueError as error:
            raise gr.Error('LAION trả về dữ liệu không hợp lệ.') from error
        if not isinstance(results, list):
            raise gr.Error('LAION không trả về danh sách ảnh; có thể API đã thay đổi.')
        urls = [row.get('url') for row in results if isinstance(row, dict)]
        urls = [url for url in urls if isinstance(url, str) and urlparse(url).scheme in ('http', 'https') and urlparse(url).netloc
                and not any(c in url for c in '<>\r\n')]
        # Browser loads remote images directly; do not populate the local gallery.
        output = '\n\n'.join(f'![Ảnh {i + 1}](<{url}>)' for i, url in enumerate(urls[:int(top_k)]))
        if not output:
            output = 'LAION không trả về ảnh phù hợp.'
        return output, f'LAION trả về {min(len(urls), int(top_k))} liên kết ảnh. Một số liên kết có thể không còn truy cập được.'


    @serialized_search
    def search(self, reference, description, top_k, upgraded=False):
        if not isinstance(reference,(str,Path)) or not str(reference).strip():
            raise gr.Error('Hãy chọn ảnh tham chiếu.')
        if not isinstance(description,str) or not description.strip():
            raise gr.Error('Hãy nhập mô tả thay đổi bằng tiếng Anh.')
        try:
            number=float(top_k)
            if not math.isfinite(number) or not number.is_integer() or not 1<=number<=self.result_limit:
                raise ValueError
            top_k=int(number)
        except (TypeError,ValueError,OverflowError):
            raise gr.Error(f'Số kết quả phải là số nguyên 1–{self.result_limit}.')
        prompt=description.strip()
        if upgraded:
            if self.source!='local':
                raise gr.Error('Bản nâng cấp hỗ trợ kho local.')
            prompt,_=adaptive_prompt(prompt)
        elif '$' not in prompt:
            prompt='a photo of $ that '+prompt
        if prompt.count('$')!=1:
            raise gr.Error('Mô tả chỉ được có một ký hiệu $.')
        prompt=prompt.replace('$',' $ ')
        if len(self.tokenizer(prompt,truncation=False).input_ids)>77:
            raise gr.Error('Mô tả vượt giới hạn 77 token của CLIP. Hãy viết ngắn hơn.')
        tokens=self.tokenizer(prompt,padding='max_length',truncation=True,max_length=77,return_tensors='pt').input_ids.to(self.device)
        if tokens.eq(259).sum().item()!=1:
            raise gr.Error('Mô tả không có đúng một pseudo-token LinCIR.')
        if self.source=='laion':
            return self.search_laion(reference,tokens,top_k)
        with self.lock,torch.inference_mode():
            try:
                image=read_image(reference)
            except (OSError,ValueError) as error:
                raise gr.Error('Không đọc được ảnh tham chiếu.') from error
            self._index()
            if not self.paths:
                raise gr.Error('Kho chưa có ảnh đọc được. Hãy thêm ảnh vào kho.')
            digest=image_digest(image)
            raw=self._fast_reference_features(image,digest) if upgraded else self._reference_features(image,digest)
            query=self._query_features(image,digest,tokens)
            negative=upgraded and is_negative(description)
            if negative:
                query=query+.1*F.normalize(raw.float(),dim=-1)
            scores=(self.features@query.T).squeeze(1)
            if not torch.isfinite(scores).all():
                raise gr.Error('Model trả về điểm không hợp lệ.')
            candidates=self._candidate_indices(reference,digest)
            if not candidates:
                raise gr.Error('Kho chỉ có ảnh giống ảnh tham chiếu. Hãy thêm ảnh khác.')
            if upgraded and not negative:
                stamp=(id(self.features),tuple(self.features.shape))
                if getattr(self,'_gate_norm_stamp',None)!=stamp:
                    self._gate_max_norm=float(self.features.norm(dim=-1).max())
                    self._gate_norm_stamp=stamp
                order=bounded_gate(self.features,scores,raw,candidates,max(top_k,50),self._gate_max_norm)[:top_k]
            elif upgraded:
                order=exact_topk(scores,candidates,top_k)
            else:
                order=[candidates[j] for j in torch.argsort(scores[candidates],descending=True,stable=True).tolist()[:top_k]]
            results=[(str(self.paths[i]),f'{self.paths[i].relative_to(self.gallery).as_posix()} | điểm: {float(scores[i]):.4f}') for i in order]
            label='Bản nâng cấp' if upgraded else 'LinCIR gốc'
            status=f'{label}: đã tìm trong {len(candidates)} ảnh ứng viên ({self.device}). Điểm là độ tương đồng, không phải xác suất.'
            if upgraded:
                status+=' Dùng truy vấn thích ứng và kết hợp điểm có giới hạn; không kiểm chứng từng ảnh. Kết quả có thể sai và không bảo đảm mọi thuộc tính.'
            if self.skipped:
                status+=f' Bỏ qua {len(self.skipped)} file ảnh không đọc được.'
            return results,status


def build_demo(retriever):
    def run_search(reference,description,top_k,mode):
        if mode not in ('Bản gốc LinCIR',UPGRADED_MODE):
            raise gr.Error('Chế độ tìm kiếm không hợp lệ.')
        if mode==UPGRADED_MODE:
            return retriever.search_upgraded(reference,description,top_k)
        return retriever.search(reference,description,top_k)
    with gr.Blocks(title='LinCIR — Tìm ảnh theo ảnh và mô tả') as app:
        gr.Markdown('# LinCIR: tìm ảnh theo ảnh tham chiếu và mô tả\nTìm ảnh có sẵn trong kho, không tạo hay chỉnh sửa ảnh.')
        if retriever.source=='laion':
            gr.Markdown('Nguồn LAION online dùng bản gốc. Vector truy vấn được gửi tới dịch vụ; dịch vụ có thể không sẵn sàng.')
        with gr.Accordion('1. Kho ảnh — thêm ảnh ứng viên trước khi tìm',open=True,visible=retriever.source=='local'):
            gr.Markdown(f'Kho ảnh: `{retriever.gallery}`')
            uploads=gr.File(label='Chọn ảnh thêm vào kho',file_count='multiple',type='filepath',file_types=['image'])
            add=gr.Button('Thêm ảnh vào kho')
            upload_status=gr.Textbox(label='Trạng thái kho',interactive=False)
            add.click(retriever.add_images,inputs=uploads,outputs=upload_status,api_name='add_images')
        with gr.Row():
            reference=gr.Image(label='2. Ảnh tham chiếu',type='filepath',sources=['upload'])
            with gr.Column():
                description=gr.Textbox(label='3. Mô tả thay đổi (tiếng Anh)',placeholder='Ví dụ: wearing a blue shirt without a hat')
                top_k=gr.Slider(1,20,value=6,step=1,label='Số kết quả tối đa')
                mode=gr.Radio(['Bản gốc LinCIR',UPGRADED_MODE],value=UPGRADED_MODE if retriever.source=='local' else 'Bản gốc LinCIR',label='Phiên bản',visible=retriever.source=='local')
                search=gr.Button('Tìm ảnh',variant='primary')
        status=gr.Textbox(label='Trạng thái tìm kiếm',interactive=False,lines=3)
        results=gr.Gallery(label='Kết quả tìm kiếm',columns=3,type='filepath') if retriever.source=='local' else gr.Markdown()
        mode.change(lambda:([], 'Đã đổi phiên bản. Nhấn Tìm ảnh để chạy lại.'),outputs=[results,status],api_name=False)
        search.click(run_search,inputs=[reference,description,top_k,mode],outputs=[results,status],api_name='search')
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gallery', default=str(ROOT / 'gallery'))
    parser.add_argument('--cache_dir', default=DEFAULT_MODEL_CACHE)
    parser.add_argument('--device', choices=['cpu', 'cuda', 'auto'], default='cpu')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--source', choices=['local', 'laion'], default='local')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Cổng phải nằm trong khoảng 1–65535.")
    try:
        retriever = LocalRetriever(args.gallery, args.cache_dir, args.device, args.source)
    except (OSError, ValueError, RuntimeError) as error:
        print(f'Không khởi động được: {error}\nXem HUONG_DAN_DEMO.md để kiểm tra môi trường và model.', file=sys.stderr)
        return 1
    print(f'Sẵn sàng. Mở http://127.0.0.1:{args.port} | Kho ảnh: {retriever.gallery}', flush=True)
    build_demo(retriever).queue().launch(server_name='127.0.0.1', server_port=args.port,
        inbrowser=not args.no_browser, share=False, allowed_paths=[str(retriever.gallery)])
    return 0


if __name__ == '__main__':
    sys.exit(main())
