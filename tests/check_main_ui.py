"""Check shared ranking and UI without model weights or networking."""
from collections import OrderedDict
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import gradio as gr
from PIL import Image
import torch
import torch.nn.functional as F
# Cho phép chạy trực tiếp file này mà không cần `python -m`.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))
from lincir.apps.demo import LocalRetriever
from lincir.apps.demo_fti import Comparison, build_demo_fti, online_gallery
from lincir.core.fti_retrieval import FTIRetriever
from lincir.core.runtime_config import ROOT

class MainUIChecks(unittest.TestCase):
    def setUp(self):
        self.picture=Image.new('RGB',(8,8),'blue')
        r=LocalRetriever.__new__(LocalRetriever)
        r.source='local';r.lock=threading.RLock();r.result_limit=20;r.device=torch.device('cpu')
        r.gallery=ROOT/'gallery'
        generator=torch.Generator().manual_seed(8)
        r.features=F.normalize(torch.randn(64,768,generator=generator),dim=-1)
        self.q=F.normalize(torch.randn(1,768,generator=generator),dim=-1)
        self.raw=torch.randn(1,768,generator=generator)
        r.paths=[r.gallery/f'{i}.jpg' for i in range(64)]
        r.skipped=[];r.signature='same local gallery';r.laion_api_url=None
        r.laion_index=SimpleNamespace(vectors=r.features.numpy(),records=[
            {'url':f'https://example.com/{i}.jpg','caption':f'image {i}'} for i in range(64)])
        r._index=Mock();r._candidate_indices=Mock(return_value=list(range(64)))
        r._reference_features=Mock(return_value=self.raw)
        r._fast_reference_features=Mock(return_value=self.raw)
        r._query_features=Mock(return_value=self.q)
        r.reference_cache=OrderedDict();r.query_cache=OrderedDict()
        def tokenize(prompt,**kwargs):
            return SimpleNamespace(input_ids=torch.tensor([[259,49407]]) if kwargs.get('return_tensors') else [259,49407])
        r.tokenizer=tokenize;self.r=r
        self.fti=FTIRetriever.__new__(FTIRetriever);self.fti.retriever=r;self.fti.cache=OrderedDict()
        self.fti.reference_tokens=Mock(return_value=(self.raw,None,None,[1]))

    def ids(self,results): return [int(Path(url).stem) for url,_ in results]

    def test_baseline_and_gated_keep_local_ranking_on_online_vectors(self):
        original=self.r.features
        with patch('lincir.apps.demo.read_image',return_value=self.picture):
            for upgraded,text in [(False,'is blue'),(True,'is blue'),(True,'without a hat')]:
                with self.subTest(upgraded=upgraded,text=text):
                    local,_=self.r.search('ref.jpg',text,6,upgraded=upgraded)
                    self.r._index.reset_mock()
                    online,status=self.r.search('ref.jpg',text,6,upgraded=upgraded,source='laion')
                    self.assertEqual(self.ids(local),self.ids(online))
                    self.r._index.assert_not_called()
                    self.assertIn('64 ảnh ứng viên của tập con LAION',status)
        self.assertIs(self.r.features,original)
        self.assertEqual(self.r.source,'local')
        self.assertIs(self.r._gallery_features('laion'),self.r.laion_features)
        self.assertTrue(torch.equal(torch.from_numpy(self.r.laion_index.vectors),original))

    def test_gated_scores_follow_existing_positive_and_negative_formulas(self):
        with patch('lincir.apps.demo.read_image',return_value=self.picture):
            for text in ['is blue','without a hat']:
                results,_=self.r.search_upgraded('ref.jpg',text,6,source='laion')
                first=(self.r.features@self.q.T).squeeze(1)
                ref=F.normalize(self.raw,dim=-1)[0]
                if text.startswith('without'):
                    expected=(self.r.features@(self.q+.1*ref).T).squeeze(1)
                else:
                    gate=torch.sigmoid((first-torch.topk(first,50).values[-1])/.01)
                    expected=first+.4*gate*(self.r.features@ref)
                self.assertEqual(self.ids(results),torch.argsort(expected,descending=True,stable=True)[:6].tolist())

    def test_fti_uses_same_query_and_ranking_for_both_sources(self):
        with patch('lincir.core.fti_retrieval.read_image',return_value=self.picture),patch('lincir.core.fti_retrieval.query',return_value=self.q):
            local,_=self.fti.search('ref.jpg','is blue',6)
            self.r._index.reset_mock()
            online,status=self.fti.search('ref.jpg','is blue',6,source='laion')
        self.assertEqual(self.ids(local),self.ids(online))
        self.assertEqual(self.ids(online),torch.argsort((self.r.features@self.q.T).flatten(),descending=True)[:6].tolist())
        self.r._index.assert_not_called();self.assertIn('tập con LAION',status)

    def test_online_comparison_runs_all_three_without_reading_result_images(self):
        controller=Comparison(self.r);controller.fti=self.fti
        with patch('lincir.apps.demo.read_image',return_value=self.picture),patch('lincir.core.fti_retrieval.read_image',return_value=self.picture),patch('lincir.apps.demo_fti.read_image',return_value=self.picture) as read,patch('lincir.core.fti_retrieval.query',return_value=self.q):
            result=controller.run('ref.jpg','is blue',6,'Ảnh mới','ignored-target.jpg','laion')
        self.assertEqual(len(result),17)
        for i in range(3):
            first,gallery,top,ranked,status=result[2+5*i:7+5*i]
            self.assertIsNone(first);self.assertEqual(gallery,[])
            self.assertEqual((top+ranked).count('<img '),7);self.assertIn('tập con LAION',status)
        read.assert_called_once_with('ref.jpg');self.r._index.assert_not_called()
        self.assertIn('FTI4CIR',result[0]);self.assertIn('Không áp dụng',result[0])

    def test_changed_inputs_discard_pending_results(self):
        controller=Comparison(self.r);controller.fti=self.fti
        def pending(*args,**kwargs):
            controller.invalidate();return [],'stale'
        self.r.search=Mock(side_effect=pending);self.fti.search=Mock(return_value=([],'stale'))
        with patch('lincir.apps.demo_fti.read_image',return_value=self.picture):
            self.assertEqual(controller.run('ref.jpg','blue',6,'Ảnh mới',source='laion'),[gr.skip() for _ in range(17)])

    def test_local_comparison_keeps_image_and_gallery_outputs(self):
        controller=Comparison(self.r);controller.fti=self.fti
        with patch('lincir.apps.demo.read_image',return_value=self.picture),patch('lincir.core.fti_retrieval.read_image',return_value=self.picture),patch('lincir.apps.demo_fti.read_image',return_value=self.picture),patch('lincir.core.fti_retrieval.query',return_value=self.q):
            result=controller.run('ref.jpg','is blue',6,'Ảnh mới')
        self.assertEqual(len(result),17)
        for i in range(3):
            first,gallery,top,ranked,status=result[2+5*i:7+5*i]
            self.assertEqual(first,gallery[0][0]);self.assertEqual(len(gallery),6)
            self.assertEqual((top,ranked),('',''));self.assertTrue(status)

    def test_online_html_escapes_metadata_and_rejects_invalid_urls(self):
        rendered=''.join(online_gallery([('https://example.com/a?x="&y=1','<script>alert(1)</script>'),('javascript:alert(1)','bad')]))
        self.assertEqual(rendered.count('<img '),2);self.assertIn('&quot;&amp;y=1',rendered)
        self.assertIn('&lt;script&gt;',rendered);self.assertNotIn('<script>',rendered);self.assertNotIn('javascript:',rendered)

    def test_online_frames_exist_before_search_and_after_reset(self):
        frames=online_gallery([])
        empty=''.join(frames)
        self.assertIn('Top 1',empty);self.assertIn('Kết quả theo thứ hạng',empty)
        self.assertIn('height:300px',empty);self.assertIn('height:430px',empty)
        self.assertNotIn('<img ',empty)
        for source in ['local','laion']:
            app=build_demo_fti(self.r,source)
            search=next(fn for fn in app.fns.values() if fn.api_name=='search')
            for i in range(3):
                for j in range(2):
                    self.assertEqual(search.outputs[4+5*i+j].value,frames[j])
                    self.assertEqual(search.outputs[4+5*i+j].visible,source=='laion')
        cleared=Comparison(self.r).invalidate()
        for i in range(3): self.assertEqual(tuple(cleared[4+5*i:6+5*i]),frames)

    def test_local_keeps_native_image_and_gallery(self):
        app=build_demo_fti(self.r)
        search=next(fn for fn in app.fns.values() if fn.api_name=='search')
        for i in range(3):
            first,gallery,top,ranked,status=search.outputs[2+5*i:7+5*i]
            self.assertIsInstance(first,gr.Image)
            self.assertIsInstance(gallery,gr.Gallery)
            self.assertEqual(gallery.height,430)
            self.assertIsInstance(top,gr.HTML);self.assertIsInstance(ranked,gr.HTML)
            self.assertEqual(top.min_height,334);self.assertEqual(ranked.min_height,430)
            self.assertIn('status-tracker',top.html_template)
            self.assertIn('height:100%',top.html_template)
            self.assertIsNone(search.show_progress_on)

    def test_source_picker_keeps_three_columns_and_clears_results(self):
        app=build_demo_fti(self.r)
        change=next(fn.fn for fn in app.fns.values() if fn.api_name=='change_source')
        search=next(fn for fn in app.fns.values() if fn.api_name=='search')
        self.assertEqual(len(search.outputs),17)
        for source,local in [('laion',False),('local',True)]:
            result=change(source);self.assertEqual(len(result),23)
            self.assertEqual([update['visible'] for update in result[:5]],[local]*5)
            for i in range(3):
                for j in range(2): self.assertEqual(result[10+5*i+j],gr.update(visible=not local,value=online_gallery([])[j]))
        with self.assertRaises(gr.Error): change('invalid')

if __name__=='__main__': unittest.main(verbosity=2)
