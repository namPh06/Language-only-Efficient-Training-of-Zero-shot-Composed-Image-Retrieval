"""Download the exact public assets used by the demos, or verify local assets."""
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
from huggingface_hub import hf_hub_download,snapshot_download,try_to_load_from_cache
import requests
from runtime_config import ROOT,DEFAULT_MODEL_CACHE

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
 return h.hexdigest()

def install(source,dest,expected):
 dest.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=dest.parent,suffix='.part');os.close(fd);tmp=Path(name)
 try:
  if isinstance(source,bytes):tmp.write_bytes(source)
  else:shutil.copyfile(source,tmp)
  if digest(tmp)!=expected:raise ValueError(f'Checksum mismatch: {dest.name}')
  os.replace(tmp,dest)
 finally:tmp.unlink(missing_ok=True)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cache-dir',default=DEFAULT_MODEL_CACHE);p.add_argument('--check',action='store_true');a=p.parse_args()
 m=json.loads((ROOT/'model_manifest.json').read_text('utf8'));missing=[]
 for item in m['sources']+m['checkpoints']:
  dest=ROOT/item['destination']
  if dest.is_file() and digest(dest)==item['sha256']:print('OK',item['destination']);continue
  if a.check:missing.append(item['destination']);continue
  if 'url' in item:
   response=requests.get(item['url'],timeout=60);response.raise_for_status();source=response.content
  else:source=hf_hub_download(item['repo'],item['filename'],revision=item['revision'],cache_dir=a.cache_dir)
  install(source,dest,item['sha256']);print('Installed',item['destination'])
 for key in ['clip','tokenizer']:
  item=m[key]
  probe='config.json' if key=='clip' else 'tokenizer_2/tokenizer_config.json'
  cached_probe=try_to_load_from_cache(item['repo'],probe,cache_dir=a.cache_dir,revision=item['revision'])
  cached_weights=try_to_load_from_cache(item['repo'],'model.safetensors',cache_dir=a.cache_dir,revision=item['revision']) if key=='clip' else cached_probe
  if key=='clip' and not isinstance(cached_weights,str):cached_weights=try_to_load_from_cache(item['repo'],'pytorch_model.bin',cache_dir=a.cache_dir,revision=item['revision'])
  required_names=['config.json'] if key=='clip' else ['tokenizer_2/vocab.json','tokenizer_2/merges.txt','tokenizer_2/tokenizer_config.json']
  has_required=all(isinstance(try_to_load_from_cache(item['repo'],n,cache_dir=a.cache_dir,revision=item['revision']),str) for n in required_names)
  if not a.check and (not has_required or not isinstance(cached_weights,str)):
   patterns=['config.json','model.safetensors'] if key=='clip' else ['tokenizer_2/*']
   snapshot_download(item['repo'],revision=item['revision'],cache_dir=a.cache_dir,allow_patterns=patterns)
  required=['config.json','model.safetensors'] if key=='clip' else ['tokenizer_2/vocab.json','tokenizer_2/merges.txt','tokenizer_2/tokenizer_config.json']
  for filename in required:
   cached=try_to_load_from_cache(item['repo'],filename,cache_dir=a.cache_dir,revision=item['revision'])
   # Existing compatible CLIP caches may store the published .bin instead.
   if key=='clip' and filename=='model.safetensors' and not isinstance(cached,str):cached=try_to_load_from_cache(item['repo'],'pytorch_model.bin',cache_dir=a.cache_dir,revision=item['revision'])
   if not isinstance(cached,str):missing.append(key+'/'+filename)
 if missing:raise SystemExit('Missing/invalid assets: '+', '.join(missing)+'\nRun: python setup_models.py')
 print('READY: model assets verified. Cache:',a.cache_dir)
if __name__=='__main__':main()
