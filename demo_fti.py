"""Presentation demo; retrieval algorithms remain unchanged."""
from runtime_config import DEFAULT_MODEL_CACHE
import argparse,sys,time,json,html
from pathlib import Path
import gradio as gr
from demo import LocalRetriever,ROOT,UPGRADED_MODE,read_image,image_digest
from fti_retrieval import FTIRetriever

class Comparison:
    def __init__(self,r): self.r=r;self.fti=None;self.round=0;self.generation=0
    def invalidate(self):
        self.generation+=1
        return ['','',*[v for _ in range(3) for v in [None,[],'']]]
    def initialize(self):
        if self.fti is None: self.fti=FTIRetriever(self.r)
    def run(self,image,text,k,timing,target=None):
        if not image or not isinstance(text,str) or not text.strip(): raise gr.Error('Chọn ảnh tham chiếu và nhập mô tả.')
        generation=self.generation
        r=self.r
        with r.lock:
            start=time.perf_counter();self.initialize();r._index()
            picture=read_image(image);digest=image_digest(picture)
            warm=timing=='Ảnh dùng lại'
            if warm:
                r._reference_features(picture,digest);self.fti.reference_tokens(picture,digest)
            setup=time.perf_counter()-start
            target_digest=image_digest(read_image(target)) if target else None
            methods=[lambda:r.search(image,text,k),lambda:r.search_upgraded(image,text,k),lambda:self.fti.search(image,text,k)]
            results={};rows={};snapshot=r.signature
            order=[(self.round+i)%3 for i in range(3)];self.round+=1
            original=r._fast_reference_features
            try:
                if not warm: r._fast_reference_features=r._reference_features
                for m in order:
                    if not warm: r.reference_cache.clear();self.fti.cache.clear()
                    r.query_cache.clear();t=time.perf_counter()
                    try:
                        gallery,status=methods[m]();elapsed=time.perf_counter()-t
                        rank=None
                        if target_digest:
                            rank=next((j+1 for j,(path,_) in enumerate(gallery) if image_digest(read_image(path))==target_digest),None)
                        decorated=[(path,f'#{j+1} '+caption+(' | ẢNH ĐỐI CHIẾU' if rank==j+1 else '')) for j,(path,caption) in enumerate(gallery)]
                        results[m]=(decorated[0][0] if decorated else None,decorated,f'{elapsed:.3f} giây | '+status)
                        rows[m]=(f'{elapsed:.3f}',str(rank) if rank else ('Không trong top-'+str(int(k)) if target_digest else 'Chưa chọn'))
                    except (ValueError,OSError,RuntimeError,gr.Error) as e:
                        results[m]=(None,[],str(e));rows[m]=('Lỗi','—')
            finally: r._fast_reference_features=original
            r._index()
            if r.signature!=snapshot: raise gr.Error('Kho ảnh đã thay đổi. Hãy chạy lại so sánh.')
            if generation!=self.generation:
                return ['', 'Đầu vào đã thay đổi. Hãy chạy lại so sánh.',*[v for _ in range(3) for v in [None,[],'']]]
            table='| Phiên bản | Thời gian (giây) | Hạng ảnh đối chiếu |\n|---|---:|---|\n'
            for i,name in enumerate(['LinCIR gốc','gated','FTI4CIR']): table+=f'| {name} | {rows[i][0]} | {rows[i][1]} |\n'
            note=f'Chuẩn bị mô hình/kho/cache: {setup:.2f} giây, tách khỏi thời gian tìm kiếm. Chế độ: {timing}. Thứ tự chạy được luân phiên; chạy tuần tự trên cùng máy, không cộng ba thời gian thành độ trễ một phiên bản.\n\nẢnh đối chiếu do người trình bày chọn, không phải hệ thống tự xác nhận đáp ứng mọi thuộc tính. Điểm tương đồng giữa các mô hình không dùng để so trực tiếp.'
            return [table,note,*[value for i in range(3) for value in results[i]]]

def benchmark_table():
    p=ROOT/'docs/results/benchmark.json'
    if not p.exists(): return 'Chưa tìm thấy kết quả benchmark đã lưu.'
    x=json.loads(p.read_text('utf8'))
    if x.get('partial') or not x.get('snapshot_verified'): return 'Kết quả benchmark chưa hoàn tất kiểm chứng.'
    text='CIRCO validation đã lưu: 220 truy vấn, 123.403 ảnh. Không phải kết quả vừa chạy trên kho demo.\n\n| Phiên bản | mAP@10 | mAP@50 |\n|---|---:|---:|\n'
    for m in ['baseline','gated','fti_clip']:
        a=x['metrics'][m];text+=f"| {m} | {a['mAP@10']:.2f} | {a['mAP@50']:.2f} |\n"
    return text+'\nFTI4CIR dùng tiền xử lý tương thích kho CLIP; kết quả validation không bảo đảm đúng mọi truy vấn.'

def build_demo_fti(r):
    controller=Comparison(r)
    with gr.Blocks(title='So sánh LinCIR, gated và FTI4CIR') as app:
        gr.Markdown('# So sánh cải tiến tìm kiếm ảnh\nCùng ảnh tham chiếu, cùng mô tả, cùng kho ảnh. Ba thuật toán trả kết quả độc lập.')
        with gr.Accordion('Kho ảnh — thêm ảnh trước khi trình bày',open=False):
            gr.Markdown(f'Kho: {r.gallery}')
            uploads=gr.File(label='Ảnh thêm vào kho',file_count='multiple',type='filepath',file_types=['image'])
            add=gr.Button('Thêm ảnh');upload_status=gr.Textbox(label='Trạng thái kho')
            add.click(r.add_images,inputs=uploads,outputs=upload_status)
        with gr.Row():
            image=gr.Image(label='Ảnh tham chiếu',type='filepath')
            with gr.Column():
                text=gr.Textbox(label='Mô tả thay đổi bằng tiếng Anh')
                gr.Examples([['is on a beach'],['wearing a blue shirt'],['wearing a shirt without a hat']],inputs=[text])
                k=gr.Slider(1,20,value=6,step=1,label='Số kết quả mỗi phiên bản')
                timing=gr.Radio(['Ảnh mới','Ảnh dùng lại'],value='Ảnh mới',label='Đo tốc độ')
                target=gr.Image(label='Ảnh đối chiếu mong muốn (tùy chọn, có trong kho)',type='filepath')
                button=gr.Button('So sánh cả ba phiên bản',variant='primary')
        table=gr.Markdown();note=gr.Markdown()
        outputs=[table,note]
        with gr.Row():
            for name in ['LinCIR gốc','gated','FTI4CIR']:
                with gr.Column():
                    gr.Markdown('## '+name)
                    first=gr.Image(label='Top 1',interactive=False,type='filepath')
                    gallery=gr.Gallery(label='Kết quả theo thứ hạng',columns=2,type='filepath',height=430)
                    status=gr.Textbox(label='Thời gian và trạng thái',interactive=False,lines=4)
                    outputs.extend([first,gallery,status])
        button.click(controller.run,inputs=[image,text,k,timing,target],outputs=outputs,concurrency_limit=1)
        for component in [image,text,k,timing,target]:
            component.change(controller.invalidate,outputs=outputs,queue=False)
        with gr.Accordion('Bằng chứng benchmark và giới hạn',open=False): gr.Markdown(benchmark_table())
    return app

def main():
    p=argparse.ArgumentParser();p.add_argument('--gallery',default=str(ROOT/'gallery'));p.add_argument('--cache_dir',default=DEFAULT_MODEL_CACHE);p.add_argument('--device',choices=['cpu'],default='cpu');p.add_argument('--port',type=int,default=8013);p.add_argument('--no-browser',action='store_true');a=p.parse_args()
    if not 1<=a.port<=65535: p.error('Cổng không hợp lệ.')
    r=LocalRetriever(a.gallery,a.cache_dir,a.device,'local')
    build_demo_fti(r).queue().launch(server_name='127.0.0.1',server_port=a.port,inbrowser=not a.no_browser,share=False,allowed_paths=[str(r.gallery)])
    return 0
if __name__=='__main__': sys.exit(main())
