"""Opt-in FTI4CIR CLIP center-crop variant; existing LinCIR and gated untouched."""
import ast,hashlib,types,sys,importlib.util,inspect
from pathlib import Path
from collections import OrderedDict
import torch
import torch.nn.functional as F
from encode_with_pseudo_tokens import _make_causal_mask
from retrieval_utils import exact_topk
from demo import read_image,image_digest
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'experiments/fti4cir'
def load_fti():
 import torch
 spec=importlib.util.spec_from_file_location('MHTransformer',OUT/'MHTransformer.py')
 m=importlib.util.module_from_spec(spec);sys.modules[m.__name__]=m;spec.loader.exec_module(m)
 n=types.ModuleType('i2t_model');n.__dict__.update(torch=torch,nn=torch.nn,F=torch.nn.functional,MHTransformer=m);sys.modules[n.__name__]=n
 a=ast.parse((OUT/'i2t_model.py').read_text());a.body=[v for v in a.body if isinstance(v,ast.ClassDef)]
 exec(compile(a,'i2t_model.py','exec'),n.__dict__)
 allowed=[n.IMG2TEXT,n.Phi,m.Transformer,m.TransformerLayer,m.MultiHeadAttention,m.MlpTransformer,set,torch.nn.functional.relu,*[getattr(torch.nn,k) for k in ['Sequential','Linear','GELU','Dropout','Sigmoid','CosineEmbeddingLoss','MSELoss','ModuleList','LayerNorm']]]
 ckpt=OUT/'FTI4CIR_model.pth'
 assert hashlib.sha256(ckpt.read_bytes()).hexdigest()=='aa1acd03fba4e70f77b6afbf296f849e58dddcb899f05e613bf677435ff1a967'
 with torch.serialization.safe_globals(allowed): model=torch.load(ckpt,weights_only=True,map_location='cpu')
 assert all(torch.isfinite(v).all() for v in model.state_dict().values())
 return model.float().eval()

@torch.inference_mode()
def prepare(r,model,image):
  pixels=r.processor(images=image,return_tensors='pt').pixel_values.to(r.device)
  vision=r.vision(pixel_values=pixels)
  raw=vision.image_embeds.float()
  patch=vision.last_hidden_state.float()
  assert patch.shape==(1,257,1024)
  # HF last_hidden_state is after all visual blocks and before post-LN,
  # corresponding to get_img_patch_feats in the published source.
  local,counts=model.get_img_local_attr_feats(raw,patch)
  sub=model.phi_s(raw);attr=model.phi_a(local)
  assert sub.shape==(1,768) and attr.shape[-1]==768
  assert all(torch.isfinite(v).all() for v in [raw,patch,sub,attr])
  return raw,sub,attr,counts

@torch.inference_mode()
def query(r,sub,attr,counts,text):
  prompt=f"a photo of * with {'* '*counts[0]}but "+text
  ids=r.tokenizer(prompt,padding='max_length',truncation=True,max_length=77,return_tensors='pt').input_ids.to(r.device)
  marker=r.tokenizer.encode('*',add_special_tokens=False)
  assert len(marker)==1
  positions=torch.nonzero(ids[0]==marker[0]).flatten()[:counts[0]+1]
  assert len(positions)==counts[0]+1
  end=int(ids.argmax(dim=-1)[0])+1;ids=ids[:,:end]
  x=r.encoder.text_model.embeddings.token_embedding(ids)
  x[:,positions[0]]=sub
  x[:,positions[1:]]=attr[:,:counts[0]]
  assert torch.isfinite(x).all()
  x=x+r.encoder.text_model.embeddings.position_embedding(r.encoder.text_model.embeddings.position_ids[:,:end])
  enc=r.encoder.text_model.encoder;mask=_make_causal_mask(ids.shape,x.dtype,x.device)
  if 'causal_attention_mask' in inspect.signature(enc.forward).parameters:
   x=enc(inputs_embeds=x,attention_mask=None,causal_attention_mask=mask)[0]
  else: x=enc(inputs_embeds=x,attention_mask=mask)[0]
  x=r.encoder.text_model.final_layer_norm(x)
  q=F.normalize(r.encoder.text_projection(x[:,end-1]),dim=-1)
  assert torch.isfinite(q).all()
  return q

class FTIRetriever:
    def __init__(self,retriever):
        if retriever.source!='local': raise ValueError('FTI4CIR requires a local gallery.')
        self.retriever=retriever
        self.model=load_fti().to(retriever.device)
        self.cache=OrderedDict()

    def reference_tokens(self,image,digest):
        if digest not in self.cache:
            self.cache[digest]=prepare(self.retriever,self.model,image)
            while len(self.cache)>16: self.cache.popitem(last=False)
        self.cache.move_to_end(digest)
        return self.cache[digest]

    def search(self,reference,description,top_k=6):
        if reference is None: raise ValueError('Hãy chọn ảnh tham chiếu.')
        if not isinstance(description,str) or not description.strip(): raise ValueError('Hãy nhập mô tả thay đổi bằng tiếng Anh.')
        if isinstance(top_k,bool) or not 1<=float(top_k)<=self.retriever.result_limit or not float(top_k).is_integer(): raise ValueError('Số kết quả không hợp lệ.')
        r=self.retriever
        with r.lock,torch.inference_mode():
            image=read_image(reference);digest=image_digest(image)
            r._index()
            if not r.paths: raise ValueError('Kho chưa có ảnh đọc được.')
            raw,sub,attr,counts=self.reference_tokens(image,digest)
            prompt=f"a photo of * with {'* '*counts[0]}but "+description.strip()
            if len(r.tokenizer(prompt,truncation=False).input_ids)>77: raise ValueError('Mô tả vượt giới hạn token CLIP. Hãy viết ngắn hơn.')
            q=query(r,sub,attr,counts,description.strip())
            scores=(r.features@q.T).squeeze(1)
            if not torch.isfinite(scores).all(): raise ValueError('Điểm tìm kiếm không hợp lệ.')
            candidates=r._candidate_indices(reference,digest)
            if not candidates: raise ValueError('Kho không có ảnh khác ảnh tham chiếu.')
            order=exact_topk(scores,candidates,int(top_k))
            results=[(str(r.paths[i]),f'{r.paths[i].name} | điểm: {float(scores[i]):.4f}') for i in order]
            return results,f'FTI4CIR thử nghiệm: tìm trong {len(candidates)} ảnh. Có lưu token của 16 ảnh tham chiếu gần nhất trong RAM. Điểm là độ tương đồng, không bảo đảm mọi thuộc tính.'
