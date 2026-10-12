"""Create a source-only shareable ZIP and SHA256 inventory."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
FILES=['.gitignore','README.md','LICENSE','NOTICE','requirements.txt','requirements-demo.txt','requirements-benchmark.txt','requirements-training.txt','runtime_config.py','setup_models.py','model_manifest.json','package_project.py','demo.py','demo_fti.py','demo_circo_showcase.py','fti_retrieval.py','upgraded_retrieval.py','retrieval_utils.py','encode_with_pseudo_tokens.py','models.py','clip_client.py','run_pretrained.py','prepare_circo.py','benchmark_circo.py','data_utils.py','loader.py','utils.py','train_phi.py','validate.py','eval_templates.py','generate_test_submission.py','example1.jpg','5. 2312.01998v2.pdf','RUN_PRETRAINED.cmd','RUN_CIRCO.cmd','CHECK_CIRCO.cmd','RUN_DEMO.cmd','gallery/.gitkeep','.github/figure_001.png']

def main():
 files=[ROOT/n for n in FILES]+sorted((ROOT/'docs').rglob('*'))
 files=[p for p in files if p.is_file()]
 missing=[n for n in FILES if not (ROOT/n).is_file()]
 if missing:raise SystemExit('Missing required source files: '+str(missing))
 out=ROOT/'dist';out.mkdir(exist_ok=True);target=out/'cir_project_github.zip'
 inventory={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(ROOT).as_posix())
  z.writestr('PACKAGE_MANIFEST.json',json.dumps(inventory,indent=2))
 with zipfile.ZipFile(target) as z:
  if z.testzip() is not None:raise RuntimeError('Invalid ZIP')
 (out/'package_manifest.json').write_text(json.dumps({'zip':target.name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'files':inventory},indent=2),'utf8')
 print(f'Created {target}: {len(files)} files, {target.stat().st_size/1024/1024:.2f} MiB')
if __name__=='__main__':main()
