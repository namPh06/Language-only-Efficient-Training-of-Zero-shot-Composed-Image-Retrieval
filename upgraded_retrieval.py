"""Experimental exact candidate bounds for gated score fusion; no production import."""
import re,torch
import torch.nn.functional as F
from retrieval_utils import exact_topk
MODE = 'Bản nâng cấp — truy vấn thích ứng + kết hợp điểm'
NEGATIVE=re.compile(r"\b(without|no|not|neither|nor|instead|except|less|fewer|remove|removed|removing|exclude|excluding|rather|lack|lacks|lacking|missing|absent|disappear|disappears|gone)\b|n't\b|\bother than\b",re.I)
def is_negative(text):return bool(NEGATIVE.search(text))
def bounded_gate(features,first,raw_reference,eligible,count,max_gallery_norm,weight=.4,tau=.01):
    reference=F.normalize(raw_reference.float(),dim=-1)[0]
    ids=torch.as_tensor(eligible,dtype=torch.long,device=first.device)
    count=min(int(count),len(ids))
    if count<=0:return []
    gate=torch.sigmoid((first-torch.topk(first,min(50,len(first))).values[-1])/tau)
    seeds=exact_topk(first,eligible,count);seed_ids=torch.tensor(seeds,device=first.device)
    seed_scores=first[seed_ids]+weight*gate[seed_ids]*(features[seed_ids]@reference)
    lower=seed_scores.min()
    # Cauchy-Schwarz provides an upper bound for every unseen reference dot product.
    bound=max_gallery_norm*reference.norm()+1e-5
    upper=first+weight*gate*bound
    candidates=ids[upper[ids]>=lower-1e-5]
    values=first[candidates]+weight*gate[candidates]*(features[candidates]@reference)
    final=first.new_full(first.shape,torch.finfo(first.dtype).min);final[candidates]=values
    first.copy_(final)
    return exact_topk(first,candidates,count)

MAX_SHORT_WORDS = 10
def adaptive_prompt(description):
    text = description.strip()
    if '$' in text:
        return text, 'Giữ câu có pseudo-token do người dùng nhập.'
    if len(re.findall(r'\b\w+\b', text)) <= MAX_SHORT_WORDS:
        return '$ , ' + text, 'Truy vấn ngắn: dùng cách diễn đạt gọn.'
    return 'a photo of $ that ' + text, 'Truy vấn dài: giữ cách diễn đạt LinCIR gốc.'
