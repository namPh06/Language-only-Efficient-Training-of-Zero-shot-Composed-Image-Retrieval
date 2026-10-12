"""Three-version CIRCO demo using the existing benchmark vector cache."""
import argparse,json
from runtime_config import DEFAULT_MODEL_CACHE
from pathlib import Path
import torch
import gradio as gr
from benchmark_circo import make_retriever
from demo_fti import build_demo_fti
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,default=ROOT/'benchmarks/CIRCO');p.add_argument('--cache-dir',default=DEFAULT_MODEL_CACHE);p.add_argument('--port',type=int,default=8015);p.add_argument('--no-browser',action='store_true');a=p.parse_args()
    if not 1<=a.port<=65535:p.error('Invalid port')
    manifest=ROOT/'docs/demo_cases.json'
    if not manifest.exists():raise SystemExit('Missing verified showcase manifest')
    cases=json.loads(manifest.read_text('utf8'))
    torch.set_num_threads(1)
    dataset=a.dataset.resolve()
    info=json.loads((dataset/'COCO2017_unlabeled/annotations/image_info_unlabeled2017.json').read_text('utf8'))
    r=make_retriever(dataset,info,a.cache_dir,'cpu',20)
    app=build_demo_fti(r)
    components={getattr(v,'label',None):v for v in app.blocks.values() if getattr(v,'label',None)}
    examples=[[str(r.gallery/f"{c['reference_img_id']:012}.jpg"),c['text'],str(r.gallery/f"{c['target_img_id']:012}.jpg")] for c in cases]
    with app:
        gr.Markdown('## Ví dụ CIRCO đã kiểm chứng\nChọn một hàng bên dưới, rồi nhấn So sánh cả ba phiên bản. Bốn ví dụ cải thiện và một ví dụ giới hạn; dùng cùng kho 123.403 ảnh. Không thêm ảnh vào kho CIRCO trong phiên demo này.')
        gr.Examples(examples,inputs=[components['Ảnh tham chiếu'],components['Mô tả thay đổi bằng tiếng Anh'],components['Ảnh đối chiếu mong muốn (tùy chọn, có trong kho)']],cache_examples=False)
    app.queue().launch(server_name='127.0.0.1',server_port=a.port,inbrowser=not a.no_browser,share=False,allowed_paths=[str(r.gallery)])
if __name__=='__main__':main()
