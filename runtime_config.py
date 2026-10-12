"""Portable shared model-cache configuration."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEFAULT_MODEL_CACHE=os.environ.get('CIR_MODEL_CACHE') or str(Path('C:/hf_cache') if os.name=='nt' and Path('C:/hf_cache').is_dir() else ROOT/'hf_models')

CLIP_REVISION="32bd64288804d66eefd0ccbe215aa642df71cc41"
TOKENIZER_REVISION="462165984030d82259a11f4367a4eed129e94a7b"
