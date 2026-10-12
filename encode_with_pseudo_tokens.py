'''
LinCIR
Copyright (c) 2023-present NAVER Corp.
CC BY-NC-4.0 (https://creativecommons.org/licenses/by-nc/4.0/)
'''
import torch
import inspect
from transformers import CLIPTextModelWithProjection


def _make_causal_mask(
    input_ids_shape: torch.Size, dtype: torch.dtype, device: torch.device, past_key_values_length: int = 0
):
    """
    Make causal mask used for bi-directional self-attention.
    Copy-paste from https://github.com/huggingface/transformers/blob/v4.34.0/src/transformers/models/clip/modeling_clip.py#L679-L693
    """
    bsz, tgt_len = input_ids_shape
    mask = torch.full((tgt_len, tgt_len), torch.finfo(dtype).min, device=device)
    mask_cond = torch.arange(mask.size(-1), device=device)
    mask.masked_fill_(mask_cond < (mask_cond + 1).view(mask.size(-1), 1), 0)
    mask = mask.to(dtype)

    if past_key_values_length > 0:
        mask = torch.cat([torch.zeros(tgt_len, past_key_values_length, dtype=dtype, device=device), mask], dim=-1)
    return mask[None, None, :, :].expand(bsz, 1, tgt_len, tgt_len + past_key_values_length)


def encode_with_pseudo_tokens_HF(clip_model: CLIPTextModelWithProjection, text: torch.Tensor, pseudo_tokens: torch.Tensor,
                              num_tokens=1, return_last_states=False) -> torch.Tensor:
    max_length = clip_model.text_model.embeddings.position_ids.shape[-1]
    if text.ndim != 2 or not 0 < text.shape[1] <= max_length:
        raise ValueError('Text must be a nonempty batch of token sequences within the CLIP context length')
    if pseudo_tokens.ndim != 2 or pseudo_tokens.shape[0] != text.shape[0]:
        raise ValueError('Pseudo tokens must contain one embedding per text sequence')
    if num_tokens != 1:
        raise ValueError('This encoder supports one pseudo-token embedding per sequence')
    x = clip_model.text_model.embeddings.token_embedding(text).type(clip_model.dtype)  # [batch_size, n_ctx, d_model]
    x = torch.where(text.unsqueeze(-1) == 259,
                    pseudo_tokens.unsqueeze(1).to(device=x.device, dtype=clip_model.dtype),
                    x)
    x = x + clip_model.text_model.embeddings.position_embedding(clip_model.text_model.embeddings.position_ids[:, :text.shape[1]])
    _causal_attention_mask = _make_causal_mask(text.shape, x.dtype, device=x.device)
    encoder = clip_model.text_model.encoder
    # Transformers 5 merges the old causal_attention_mask into attention_mask.
    # Passing the removed keyword is silently ignored through **kwargs.
    if 'causal_attention_mask' in inspect.signature(encoder.forward).parameters:
        x = encoder(inputs_embeds=x, attention_mask=None,
                    causal_attention_mask=_causal_attention_mask,
                    output_attentions=False, output_hidden_states=False)
    else:
        x = encoder(inputs_embeds=x, attention_mask=_causal_attention_mask)
    x = x[0]
    x_last = clip_model.text_model.final_layer_norm(x)
    x = x_last[torch.arange(x_last.shape[0], device=x_last.device),
          text.to(dtype=torch.int, device=x_last.device).argmax(dim=-1),
          ]
    if hasattr(clip_model, 'text_projection'):
        x = clip_model.text_projection(x)

    if return_last_states:
        return x, x_last
    else:
        return x


def tokenize_retrieval_text(clip_model, texts, context_length=77):
    """Use the same CLIP vocabulary as the HF model, retaining the $ marker."""
    tokenizer = getattr(clip_model, 'retrieval_tokenizer', None)
    if tokenizer is None:
        # Compatibility for callers supplying a model without its tokenizer.
        import clip
        return clip.tokenize(texts, context_length=context_length, truncate=True)
    texts = [texts] if isinstance(texts, str) else list(texts)
    texts = [text.replace('$', ' $ ') for text in texts]
    tokens = tokenizer(texts, padding='max_length', truncation=True,
                       max_length=context_length, return_tensors='pt')['input_ids']
    marker = tokenizer.get_vocab().get('[$]')
    return torch.where(tokens == marker, 259, tokens) if marker is not None else tokens
