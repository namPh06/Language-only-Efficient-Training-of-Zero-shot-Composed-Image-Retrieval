"""Presentation demo; retrieval algorithms remain unchanged."""
# Cho phép chạy trực tiếp file này mà không cần `python -m`.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from lincir.core.runtime_config import DEFAULT_MODEL_CACHE
import argparse,sys,time,json,html
from pathlib import Path
import gradio as gr
from lincir.apps.demo import LocalRetriever,ROOT,UPGRADED_MODE,read_image,image_digest
from lincir.core.fti_retrieval import FTIRetriever
from lincir.core.laion_online import DEFAULT_INDEX, image_url

LAION_PROGRESS_CSS='''
.block.laion-top { min-height:334px !important; }
.block.laion-ranked { min-height:430px !important; }
.block:is(.laion-top,.laion-ranked) > [data-testid="status-tracker"] {
    inset:0; width:100%; height:100%; border:1px solid var(--border-color-primary,#ddd); border-radius:8px;
    background:var(--block-background-fill,white);
}
.block:is(.laion-top,.laion-ranked) > [data-testid="status-tracker"] .progress-text {
    top:auto; bottom:8px; right:8px; transform:none;
}
'''

def online_gallery(records):
    cards=[]
    top=''
    icon='<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8" cy="8" r="1.5"/><path d="m3 17 6-6 4 4 3-3 5 5"/></svg>'
    placeholder=f'<div aria-hidden="true" style="height:100%;display:flex;align-items:center;justify-content:center;color:var(--body-text-color-subdued,#999)">{icon}</div>'
    for url,caption in records:
        if not image_url(url): continue
        url=html.escape(url,quote=True)
        caption=html.escape(caption,quote=True)
        if not cards:
            top=f'<a href="{url}" target="_blank" rel="noopener noreferrer" title="{caption}"><img src="{url}" alt="Top 1" style="display:block;width:100%;height:300px;object-fit:contain"></a>'
        cards.append(f'<a href="{url}" target="_blank" rel="noopener noreferrer" title="{caption}" style="display:block;position:relative;min-width:0;height:180px;color:inherit;text-decoration:none;border:1px solid var(--border-color-primary,#ddd);border-radius:6px;overflow:hidden;background:var(--background-fill-secondary,#f7f7f7)"><img src="{url}" loading="lazy" alt="Ảnh kết quả {len(cards)+1}" style="display:block;width:100%;height:100%;object-fit:contain"><div style="position:absolute;bottom:0;left:0;right:0;background:var(--block-background-fill,white);padding:4px 6px;font-size:12px;line-height:18px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{caption}</div></a>')
    frame='position:relative;border:1px solid var(--border-color-primary,#ddd);border-radius:8px;overflow:hidden;background:var(--block-background-fill,white)'
    label='display:flex;align-items:center;gap:6px;width:fit-content;height:32px;box-sizing:border-box;padding:6px 8px;border-right:1px solid var(--border-color-primary,#ddd);border-bottom:1px solid var(--border-color-primary,#ddd);border-bottom-right-radius:4px;color:var(--body-text-color-subdued,#666);font-size:12px'
    ranked=('<div style="height:100%;overflow-y:auto;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));grid-auto-rows:180px;align-content:start;gap:8px;padding:8px;box-sizing:border-box">'+''.join(cards)+'</div>') if cards else placeholder
    return (f'<section aria-label="Top 1 LAION" style="{frame}"><span style="{label}">{icon}Top 1</span><div style="height:300px">'+(top or placeholder)+'</div></section>',
            f'<section aria-label="Kết quả theo thứ hạng LAION" style="{frame};height:430px;box-sizing:border-box"><span style="{label}">{icon}Kết quả theo thứ hạng</span><div style="height:calc(100% - 32px)">'+ranked+'</div></section>')

class Comparison:
    def __init__(self,r): self.r=r;self.fti=None;self.round=0;self.generation=0
    def invalidate(self):
        self.generation+=1
        return ['','',*[v for _ in range(3) for v in [None,[],*online_gallery([]),'']]]
    def initialize(self):
        if self.fti is None: self.fti=FTIRetriever(self.r)
    def run(self,image,text,k,timing,target=None,source='local'):
        if source not in ('local','laion'): raise gr.Error('Nguồn ảnh không hợp lệ.')
        if not image or not isinstance(text,str) or not text.strip(): raise gr.Error('Chọn ảnh tham chiếu và nhập mô tả.')
        generation=self.generation
        r=self.r
        with r.lock:
            start=time.perf_counter();self.initialize();r._gallery_features(source)
            picture=read_image(image);digest=image_digest(picture)
            warm=timing=='Ảnh dùng lại'
            if warm:
                r._reference_features(picture,digest);self.fti.reference_tokens(picture,digest)
            setup=time.perf_counter()-start
            target_digest=image_digest(read_image(target)) if target and source=='local' else None
            methods=[lambda:r.search(image,text,k,source=source),lambda:r.search_upgraded(image,text,k,source=source),lambda:self.fti.search(image,text,k,source=source)]
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
                        results[m]=((decorated[0][0] if decorated else None,decorated,'','') if source=='local' else (None,[],*online_gallery(decorated)))+(f'{elapsed:.3f} giây | '+status,)
                        rows[m]=(f'{elapsed:.3f}',str(rank) if rank else ('Không áp dụng' if source=='laion' else 'Không trong top-'+str(int(k)) if target_digest else 'Chưa chọn'))
                    except (ValueError,OSError,RuntimeError,gr.Error) as e:
                        results[m]=(None,[],*online_gallery([]),str(e));rows[m]=('Lỗi','—')
            finally: r._fast_reference_features=original
            if source=='local':
                r._index()
                if r.signature!=snapshot: raise gr.Error('Kho ảnh đã thay đổi. Hãy chạy lại so sánh.')
            if generation!=self.generation:
                return [gr.skip() for _ in range(17)]
            table='| Phiên bản | Thời gian (giây) | Hạng ảnh đối chiếu |\n|---|---:|---|\n'
            for i,name in enumerate(['LinCIR gốc','gated','FTI4CIR']): table+=f'| {name} | {rows[i][0]} | {rows[i][1]} |\n'
            note=f'Chuẩn bị mô hình/kho/cache: {setup:.2f} giây, tách khỏi thời gian tìm kiếm. Chế độ: {timing}. Thứ tự chạy được luân phiên; chạy tuần tự trên cùng máy, không cộng ba thời gian thành độ trễ một phiên bản.\n\nẢnh đối chiếu do người trình bày chọn, không phải hệ thống tự xác nhận đáp ứng mọi thuộc tính. Điểm tương đồng giữa các mô hình không dùng để so trực tiếp.'
            if source=='laion':
                note=f'Chuẩn bị mô hình/kho/cache: {setup:.2f} giây, tách khỏi thời gian tìm kiếm. Chế độ: {timing}. Ba phương pháp dùng cùng tập vector LAION, chạy tuần tự với thứ tự luân phiên. Ảnh hiển thị trực tiếp từ URL gốc. Thời gian chưa gồm tải ảnh trên trình duyệt; không có nhãn đáp án LAION để tính hạng ảnh đối chiếu. Điểm tương đồng giữa các mô hình không dùng để so trực tiếp.'
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

def build_demo_fti(r,source='local'):
    controller=Comparison(r)
    local=source=='local'
    def source_description(value):
        return ('So sánh LinCIR gốc, gated và FTI4CIR trên cùng kho ảnh local.' if value=='local' else
                'So sánh LinCIR gốc, gated và FTI4CIR trên cùng tập vector LAION. Ảnh hiển thị từ website gốc; một số liên kết có thể không còn hoạt động.')
    with gr.Blocks(title='So sánh LinCIR, gated và FTI4CIR') as app:
        gr.Markdown('# Tìm kiếm ảnh theo ảnh tham chiếu và mô tả\nChọn nguồn ảnh, tải ảnh tham chiếu và nhập mô tả thay đổi.')
        source_picker=gr.Radio([('Kho ảnh local','local'),('LAION online','laion')],value=source,label='Nguồn ảnh')
        source_note=gr.Markdown(source_description(source))
        with gr.Accordion('Kho ảnh — thêm ảnh trước khi trình bày',open=False,visible=local) as upload_section:
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
                target=gr.Image(label='Ảnh đối chiếu mong muốn (tùy chọn, có trong kho)',type='filepath',visible=local)
                button=gr.Button('So sánh cả ba phiên bản',variant='primary')
        table=gr.Markdown();note=gr.Markdown()
        outputs=[table,note];local_groups=[]
        with gr.Row():
            for name in ['LinCIR gốc','gated','FTI4CIR']:
                with gr.Column():
                    gr.Markdown('## '+name)
                    with gr.Column(visible=local) as local_group:
                        first=gr.Image(label='Top 1',interactive=False,type='filepath')
                        gallery=gr.Gallery(label='Kết quả theo thứ hạng',columns=2,type='filepath',height=430)
                    online_first,online_ranked=online_gallery([])
                    online_first=gr.HTML(value=online_first,visible=not local,min_height=334,elem_classes='laion-top',
                                        html_template='<style>'+LAION_PROGRESS_CSS+'</style>${value}')
                    online_ranked=gr.HTML(value=online_ranked,visible=not local,min_height=430,elem_classes='laion-ranked')
                    status=gr.Textbox(label='Thời gian và trạng thái',interactive=False,lines=4)
                    local_groups.append(local_group)
                    outputs.extend([first,gallery,online_first,online_ranked,status])
        def change_source(value):
            if value not in ('local','laion'): raise gr.Error('Nguồn ảnh không hợp lệ.')
            local=value=='local'
            cleared=controller.invalidate()
            for i in range(3):
                for j in (4,5): cleared[j+5*i]=gr.update(visible=not local,value=cleared[j+5*i])
            return [*[gr.update(visible=local) for _ in range(5)],source_description(value),*cleared]
        source_picker.change(change_source,inputs=source_picker,
            outputs=[upload_section,target,*local_groups,source_note,*outputs],
            queue=False,api_name='change_source')
        button.click(controller.run,inputs=[image,text,k,timing,target,source_picker],outputs=outputs,
                     concurrency_limit=1,api_name='search')
        for component in [image,text,k,timing,target]:
            component.change(controller.invalidate,outputs=outputs,queue=False)
        with gr.Accordion('Bằng chứng benchmark và giới hạn',open=False): gr.Markdown(benchmark_table())
    return app

def main():
    p=argparse.ArgumentParser();p.add_argument('--gallery',default=str(ROOT/'gallery'));p.add_argument('--cache_dir',default=DEFAULT_MODEL_CACHE);p.add_argument('--device',choices=['cpu'],default='cpu');p.add_argument('--port',type=int,default=8013);p.add_argument('--no-browser',action='store_true')
    p.add_argument('--source',choices=['local','laion'],default='local')
    p.add_argument('--laion-index',type=Path,default=DEFAULT_INDEX)
    p.add_argument('--laion-api-url')
    a=p.parse_args()
    if not 1<=a.port<=65535: p.error('Cổng không hợp lệ.')
    r=LocalRetriever(a.gallery,a.cache_dir,a.device,'local',laion_index=a.laion_index,laion_api_url=a.laion_api_url)
    build_demo_fti(r,a.source).queue().launch(server_name='127.0.0.1',server_port=a.port,inbrowser=not a.no_browser,share=False,allowed_paths=[str(r.gallery)])
    return 0
if __name__=='__main__': sys.exit(main())
