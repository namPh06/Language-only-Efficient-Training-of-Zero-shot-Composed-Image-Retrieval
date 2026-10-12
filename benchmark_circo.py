"""Evaluate the original and upgraded retrievers on the complete CIRCO gallery."""
from runtime_config import DEFAULT_MODEL_CACHE
import argparse
import faulthandler
import hashlib
import json
import math
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parent
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from prepare_circo import atomic_bytes, validate_dataset

MODES = ('baseline', 'gated', 'fti_clip')
RANKS = (5, 10, 25, 50)


def save_json(path, value):
    atomic_bytes(path, json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).encode('utf-8'))


def query_metrics(predictions, row):
    if len(predictions) != len(set(predictions)):
        raise ValueError('Duplicate predictions')
    gt = set(map(int, row['gt_img_ids']))
    if not gt:
        raise ValueError('Empty ground truth')
    result = {}
    for k in RANKS:
        hits, total_precision = 0, 0.0
        for rank, image_id in enumerate(predictions[:k], 1):
            if image_id in gt:
                hits += 1
                total_precision += hits / rank
        result[f'AP@{k}'] = total_precision / min(k, len(gt))
        # Official CIRCO Recall uses ONLY target_img_id, not any ground truth.
        result[f'Recall@{k}'] = float(int(row['target_img_id']) in predictions[:k])
        result[f'GTRecall@{k}'] = hits / len(gt)
    return result


def summarize(outcomes, modes):
    summary = {}
    for mode in modes:
        values = [outcome['modes'][mode] for outcome in outcomes]
        if not values:
            continue
        metrics = {key.replace('AP@', 'mAP@'): 100 * statistics.mean(v['metrics'][key] for v in values)
                   for key in values[0]['metrics']}
        metrics['median_seconds'] = statistics.median(v['seconds'] for v in values)
        metrics['mean_result_count'] = statistics.mean(len(v['predictions']) for v in values)
        aspects = sorted({a for outcome in outcomes for a in outcome['semantic_aspects']})
        metrics['semantic_mAP@10'] = {
            aspect: 100 * statistics.mean(outcome['modes'][mode]['metrics']['AP@10']
                for outcome in outcomes if aspect in outcome['semantic_aspects']) for aspect in aspects}
        summary[mode] = metrics
    return summary


def make_retriever(dataset, image_info, cache_dir, device, batch_size, index_dir=None):
    import numpy as np
    import torch
    import torch.nn.functional as F
    from demo import LocalRetriever, read_image

    class BenchmarkRetriever(LocalRetriever):
        """Fixed official IDs, batched resumable index; no per-query filesystem scan."""
        def __init__(self):
            super().__init__(dataset / 'COCO2017_unlabeled/unlabeled2017', cache_dir, device,
                             result_limit=50, exclude_reference_by_id=True, write_search_artifacts=False)
            self.paths = [(self.gallery / row['file_name']).resolve() for row in image_info['images']]
            self.image_ids = [int(row['id']) for row in image_info['images']]
            self.path_to_id = dict(zip(self.paths, self.image_ids))
            # Pixel duplicates retain their distinct official IDs in CIRCO.
            self.digests = [str(image_id) for image_id in self.image_ids]
            self.signature = tuple((str(path), path.stat().st_size, path.stat().st_mtime_ns) for path in self.paths)
            self.features = None

        @torch.inference_mode()
        def _index(self):
            if self.features is not None:
                return
            version = 'circo-clip-large-pil224-normalized-v1'
            signature = hashlib.sha256(json.dumps([version, self.signature]).encode()).hexdigest()
            folder = Path(index_dir) if index_dir is not None else ROOT / 'outputs/circo_index'
            folder.mkdir(parents=True, exist_ok=True)
            matrix_path, state_path = folder / (signature + '.npy'), folder / (signature + '.json')
            completed = 0
            if state_path.exists() and matrix_path.exists():
                state = json.loads(state_path.read_text('utf-8'))
                completed = state['completed']
                if state['signature'] != signature or type(completed) is not int or not 0 <= completed <= len(self.paths):
                    raise ValueError('Invalid index state; remove the affected circo_index cache and retry')
                matrix = np.lib.format.open_memmap(matrix_path, mode='r+')
                if matrix.dtype != np.float32 or matrix.shape != (len(self.paths), 768):
                    raise ValueError('Invalid index shape/dtype')
                prefix = matrix[:completed]
                if not np.isfinite(prefix).all() or not np.allclose(np.linalg.norm(prefix, axis=1), 1, atol=.01):
                    raise ValueError('Invalid index vectors')
                print(f'Resuming index: {completed}/{len(self.paths)} saved images', flush=True)
            else:
                matrix = np.lib.format.open_memmap(matrix_path, mode='w+', dtype=np.float32,
                                                  shape=(len(self.paths), 768))
            for start in range(completed, len(self.paths), batch_size):
                paths = self.paths[start:start + batch_size]
                # Persist the active batch before native model calls: a DLL crash
                # bypasses Python exceptions, but the last committed prefix is safe.
                save_json(state_path, {'signature': signature, 'completed': completed,
                    'total': len(self.paths), 'active_batch': [path.name for path in paths]})
                images = [read_image(path) for path in paths]  # Fail on unreadable images, never silently skip.
                vectors = F.normalize(self._features(images).float(), dim=-1)
                if not torch.isfinite(vectors).all() or not torch.allclose(vectors.norm(dim=1),
                        torch.ones(len(paths), device=vectors.device), atol=.01):
                    raise ValueError('Invalid model vectors')
                matrix[start:start + len(paths)] = vectors.cpu().numpy()
                matrix.flush()
                completed = start + len(paths)
                save_json(state_path, {'signature': signature, 'completed': completed, 'total': len(self.paths)})
                if start == 0 or completed % (batch_size * 20) == 0 or completed == len(self.paths):
                    print(f'Index: {completed}/{len(self.paths)}', flush=True)
            self.features = torch.from_numpy(np.array(matrix)).to(self.device)
            del matrix

        def assert_snapshot(self):
            current = tuple((str(path), path.stat().st_size, path.stat().st_mtime_ns) for path in self.paths)
            if current != self.signature:
                raise RuntimeError('Dataset changed during evaluation; results are not valid')

    return BenchmarkRetriever()


def run_mode(retriever,row,mode,args):
    reference=args.image_paths[int(row['reference_img_id'])]
    if mode=='baseline':
        results,status=retriever.search(str(reference),row['relative_caption'],50)
    elif mode=='gated':
        results,status=retriever.search_upgraded(str(reference),row['relative_caption'],50)
    elif mode=='fti_clip':
        results,status=args.fti.search(str(reference),row['relative_caption'],50)
    else:
        raise ValueError('Unsupported mode')
    predictions=[retriever.path_to_id[Path(path).resolve()] for path,_ in results]
    if len(predictions)>50 or int(row['reference_img_id']) in predictions:
        raise ValueError('Invalid benchmark predictions')
    return predictions,status


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,default=ROOT/'benchmarks/CIRCO')
    parser.add_argument('--modes',nargs='+',choices=MODES,default=list(MODES))
    parser.add_argument('--limit',type=int,default=0,help='0: all 220 queries')
    parser.add_argument('--batch-size',type=int,default=1)
    parser.add_argument('--cpu-threads',type=int,default=1)
    parser.add_argument('--device',choices=('cpu','cuda','auto'),default='cpu')
    parser.add_argument('--cache-dir',default=DEFAULT_MODEL_CACHE)
    parser.add_argument('--independent-latency',action='store_true')
    parser.add_argument('--prepared-reference-latency',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/circo_final_comparison.json')
    args=parser.parse_args()
    if not 0<=args.limit<=220 or not 1<=args.batch_size<=64 or not 1<=args.cpu_threads<=64:
        parser.error('Invalid limit/batch-size/cpu-threads')
    args.dataset=args.dataset.resolve();args.output=args.output.resolve()
    if args.output.suffix.lower()!='.json' or args.output.is_relative_to(args.dataset) or args.output.is_relative_to(ROOT/'pretrained_models'):
        parser.error('Output must be .json outside dataset/model directories')
    modes=list(dict.fromkeys(args.modes))
    print('Checking full official gallery...',flush=True)
    ready=validate_dataset(args.dataset)
    if not ready['ready']:
        parser.error(f'Dataset not ready: {ready}')
    info=json.loads((args.dataset/'COCO2017_unlabeled/annotations/image_info_unlabeled2017.json').read_text('utf-8'))
    rows=json.loads((args.dataset/'annotations/val.json').read_text('utf-8'))
    selected=rows[:args.limit] if args.limit else rows
    gallery=args.dataset/'COCO2017_unlabeled/unlabeled2017'
    snapshot=[(r['id'],(gallery/r['file_name']).stat().st_size,(gallery/r['file_name']).stat().st_mtime_ns) for r in info['images']]
    files=['benchmark_circo.py','prepare_circo.py','demo.py','retrieval_utils.py','upgraded_retrieval.py','encode_with_pseudo_tokens.py','models.py']
    config={'dataset':str(args.dataset),'gallery_count':len(info['images']),'query_ids':[r['id'] for r in selected],
            'modes':modes,'device':args.device,'batch_size':args.batch_size,'cpu_threads':args.cpu_threads,
            'independent_latency':args.independent_latency,'prepared_reference_latency':args.prepared_reference_latency,
            'cache_dir':args.cache_dir,'full_text_context':os.environ.get('LINCIR_FULL_TEXT_CONTEXT')=='1',
            'gallery_hash':hashlib.sha256(json.dumps(snapshot).encode()).hexdigest(),
            'code_hash':hashlib.sha256(b''.join((ROOT/n).read_bytes() for n in files)).hexdigest(),
            'checkpoint_hash':hashlib.sha256((ROOT/'pretrained_models/lincir_large.pt').read_bytes()).hexdigest(),
            'annotations_hash':hashlib.sha256((args.dataset/'annotations/val.json').read_bytes()).hexdigest()}
    if 'fti_clip' in modes:
        config['fti_checkpoint_hash']=hashlib.sha256((ROOT/'experiments/fti4cir/FTI4CIR_model.pth').read_bytes()).hexdigest()
        config['fti_code_hash']=hashlib.sha256(b''.join((ROOT/n).read_bytes() for n in ['fti_retrieval.py','experiments/fti4cir/i2t_model.py','experiments/fti4cir/MHTransformer.py'])).hexdigest()
        config['fti_preprocessing']='CLIP standard center-crop224 variant, not official targetpad'
    if 'gated' in modes:
        config['upgraded_method']='input-negation-gated-reference-exact-bound-v1'
        config['upgraded_parameters']={'positive_weight':.4,'negative_weight':.1,'tau':.01}
    outcomes=[]
    if args.output.exists():
        saved=json.loads(args.output.read_text('utf-8'))
        if saved['config']!=config:
            parser.error('Existing output differs; use a new output path')
        outcomes=saved['queries']
        if [r['id'] for r in outcomes]!=[r['id'] for r in selected[:len(outcomes)]] or any(set(r['modes'])!=set(modes) for r in outcomes):
            parser.error('Invalid resume records')
    faulthandler.enable(all_threads=True)
    started=time.perf_counter()
    retriever=make_retriever(args.dataset,info,args.cache_dir,args.device,args.batch_size)
    import torch
    torch.set_num_threads(args.cpu_threads)
    retriever._index()
    if 'fti_clip' in modes:
        from fti_retrieval import FTIRetriever
        args.fti=FTIRetriever(retriever)
    index_seconds=time.perf_counter()-started
    args.image_paths=dict(zip(retriever.image_ids,retriever.paths))
    prep_seconds=0.
    notes=['CIRCO validation, full 123403-image gallery; metrics in percent.',
           'Inference receives reference image and relative caption only; no ground truth or shared concept.',
           'Official Recall uses target_img_id; GTRecall uses all gt_img_ids.',
           'Index/model startup and shared reference preparation are separate from query latency.',
           'Validation was used during development; these are not independent paper test results.']
    def persist(verified):
        save_json(args.output,{'benchmark':'CIRCO validation','config':config,'snapshot_verified':verified,
                  'partial':len(outcomes)!=220,'completed_queries':len(outcomes),
                  'model_and_index_seconds_this_run':index_seconds,
                  'shared_reference_preparation_seconds_this_run':prep_seconds,
                  'metrics':summarize(outcomes,modes),'queries':outcomes,'notes':notes})
    for number,row in enumerate(selected[len(outcomes):],len(outcomes)):
        outcome={'id':row['id'],'reference_img_id':row['reference_img_id'],'relative_caption':row['relative_caption'],
                 'semantic_aspects':row.get('semantic_aspects',[]),'modes':{}}
        order=modes[number%len(modes):]+modes[:number%len(modes)]
        for mode in order:
            if args.independent_latency or args.prepared_reference_latency:
                retriever.reference_cache.clear();retriever.query_cache.clear()
                if 'fti_clip' in modes: args.fti.cache.clear()
            if args.prepared_reference_latency:
                from demo import read_image,image_digest
                prepare_started=time.perf_counter()
                image=read_image(args.image_paths[int(row['reference_img_id'])])
                if mode=='fti_clip': args.fti.reference_tokens(image,image_digest(image))
                else: retriever._fast_reference_features(image,image_digest(image))
                prep_seconds+=time.perf_counter()-prepare_started
            query_started=time.perf_counter()
            predictions,status=run_mode(retriever,row,mode,args)
            outcome['modes'][mode]={'predictions':predictions,'metrics':query_metrics(predictions,row),
                                    'seconds':time.perf_counter()-query_started,'status':status}
            print(f'Query {number+1}/{len(selected)} [{mode}]: {len(predictions)} results',flush=True)
        outcomes.append(outcome);persist(False)
    retriever.assert_snapshot();persist(True)
    for mode in modes:
        save_json(args.output.with_name(args.output.stem+'_'+mode+'_predictions.json'),{str(r['id']):r['modes'][mode]['predictions'] for r in outcomes})
    print(json.dumps(summarize(outcomes,modes),ensure_ascii=False,indent=2),flush=True)
    return 0


def run_with_deadline(timeout_seconds=1200):
    """Hard wall-clock deadline includes setup and native calls on Windows."""
    import subprocess
    command=[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'--_benchmark_worker',*sys.argv[1:]]
    process=subprocess.Popen(command,cwd=ROOT)
    try:
        return process.wait(timeout=timeout_seconds)
    except (subprocess.TimeoutExpired,KeyboardInterrupt) as error:
        if os.name=='nt':
            subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:
            process.kill()
        process.wait()
        print('Benchmark stopped. Completed query records remain in the output; partial results are not a full benchmark.',flush=True)
        return 124 if isinstance(error,subprocess.TimeoutExpired) else 130


if __name__=='__main__':
    if '--_benchmark_worker' in sys.argv:
        sys.argv.remove('--_benchmark_worker')
        raise SystemExit(main())
    raise SystemExit(run_with_deadline())
