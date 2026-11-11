"""Create a source-only shareable ZIP and SHA256 inventory."""
import hashlib,json,zipfile
# Cho phép chạy trực tiếp file này mà không cần `python -m`.
import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parents[2]))
from lincir.core.runtime_config import ROOT
ONLINE_FILES=['lincir/core/laion_online.py','lincir/data/prepare_laion.py','requirements/requirements-online.txt','scripts/RUN_LAION.cmd','tests/check_laion.py','tests/check_main_ui.py']
PACKAGE_FILES=['lincir/__init__.py','lincir/core/__init__.py','lincir/apps/__init__.py','lincir/data/__init__.py','lincir/training/__init__.py','tests/__init__.py']
CORE=['runtime_config','fti_retrieval','upgraded_retrieval','retrieval_utils','encode_with_pseudo_tokens','models','clip_client']
APPS=['demo','demo_fti','demo_circo_showcase','run_pretrained']
DATA=['setup_models','package_project','prepare_circo','benchmark_circo']
TRAINING=['data_utils','loader','utils','train_phi','validate','eval_templates','generate_test_submission']
FILES=['.gitignore','README.md','LICENSE','NOTICE','model_manifest.json',
 'requirements/requirements.txt','requirements/requirements-demo.txt','requirements/requirements-benchmark.txt','requirements/requirements-training.txt',
 *PACKAGE_FILES,
 *[f'lincir/core/{n}.py' for n in CORE],*[f'lincir/apps/{n}.py' for n in APPS],
 *[f'lincir/data/{n}.py' for n in DATA],*[f'lincir/training/{n}.py' for n in TRAINING],
 'assets/example1.jpg','assets/5. 2312.01998v2.pdf',
 'scripts/RUN_PRETRAINED.cmd','scripts/RUN_CIRCO.cmd','scripts/CHECK_CIRCO.cmd','scripts/RUN_DEMO.cmd',
 'gallery/.gitkeep','.github/figure_001.png']

def main():
 files=[ROOT/n for n in FILES+ONLINE_FILES]+sorted((ROOT/'docs').rglob('*'))
 files=[p for p in files if p.is_file()]
 missing=[n for n in FILES+ONLINE_FILES if not (ROOT/n).is_file()]
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
