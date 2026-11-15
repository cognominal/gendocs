# Sparse Attention in Transformers

*From the quadratic bottleneck to production long-context systems.*

This document assumes no prior knowledge of LLM internals, but it does not
assume the reader is new to programming or linear algebra. Part I builds the
minimum background — what a transformer language model is, how it is trained
and run, and how the field got here. Part II is the actual subject: what sparse
attention is, where the design space comes from, why most "sparse" configurations
are slower than they look, and what the measurements say.

**Verification note.** No benchmarks were run for this write-up. Numbers marked
`[computed]` were derived from the formulas in the text; everything else is
attributed to the cited paper. Where a claim is an inference of mine rather
than a result, it is marked `[inference]`.

---

## Contents

- [Part I — Prerequisites](#part-i--prerequisites)
  - [1. What a language model actually computes](#1-what-a-language-model-actually-computes)
  - [2. Prefill, decode, and the KV cache](#2-prefill-decode-and-the-kv-cache)
  - [3. A short history of LLMs](#3-a-short-history-of-llms)
  - [4. Why long context is expensive](#4-why-long-context-is-expensive)
  - [5. The space of fixes](#5-the-space-of-fixes)
- [Part II — Sparse attention](#part-ii--sparse-attention)
  - [6. Definition and cost model](#6-definition-and-cost-model)
  - [7. A gallery of patterns](#7-a-gallery-of-patterns)
  - [8. Taxonomy](#8-taxonomy)
  - [9. Chronology of methods](#9-chronology-of-methods)
  - [10. Kernels: why declared sparsity is not speed](#10-kernels-why-declared-sparsity-is-not-speed)
  - [11. What the measurements say](#11-what-the-measurements-say)
  - [12. Failure modes](#12-failure-modes)
  - [13. Choosing a design](#13-choosing-a-design)
  - [14. Reference implementations and checks](#14-reference-implementations-and-checks)
  - [15. Glossary](#15-glossary)
  - [16. References](#16-references)

## TL;DR

- A transformer's self-attention compares every token with every other token.
  Cost is quadratic in sequence length; at 128K tokens this dominates
  everything else in a forward pass.
- Sparse attention computes only a subset of those comparisons. Each query
  attends to $k \ll n$ keys, turning $O(n^2)$ into $O(nk)$.
- The hard part is not the pattern. It is (a) choosing $S(i)$ without spending
  quadratic time deciding, and (b) making a GPU execute an irregular pattern
  faster than the dense kernel it replaces.
- There are two distinct worlds: **trainable sparsity** (a different model,
  trained with the pattern — NSA, MoBA, DeepSeek's DSA, sliding-window layers
  in Gemma 3 and gpt-oss) and **training-free sparsity** (approximating a dense
  pretrained model at inference — MInference, Quest, SnapKV, H2O, StreamingLLM).
- Block granularity (64–256 tokens) is the price of hardware efficiency. Fine-
  grained selection is more accurate and usually slower.
- Bigger sparse models beat smaller dense ones at equal cost, and longer
  sequences tolerate higher sparsity (Nawrot et al., ACL 2026). Fixed budgets
  in production are therefore leaving quality on the table.
- Attention sparsity cannot fix what it does not touch: MLP cost, parameter
  count, or retrieval failure ("lost in the middle"). If attention is 30% of
  your prefill time, the maximum speedup is 3.3×.

---

# Part I — Prerequisites

## 1. What a language model actually computes

### 1.1 Tokens become vectors

Text is split into **tokens** — subword units, typically 3–4 characters of
English — by a tokenizer (BPE, WordPiece, SentencePiece). A 1M-token context
is roughly 750,000 words. Each token ID indexes a row of an embedding matrix
$E \in \mathbb{R}^{V \times d}$, where $V$ is the vocabulary (32K–256K) and $d$
the model width (1,024 for a 1B model, 8,192 for a 70B model). The result is a
matrix $X \in \mathbb{R}^{n \times d}$ for a sequence of $n$ tokens.

Position is injected separately: either added to the embeddings (learned
absolute positions, sinusoidal) or applied inside attention to the queries and
keys (RoPE, ALiBi). This matters later: if you select a subset of keys, the
positional signal attached to those keys must still make sense.

### 1.2 The block

A transformer is a stack of $L$ identical blocks (32 for an 8B model, 80 for a
70B model). Each block does:

1. **Layer norm** (usually pre-norm).
2. **Self-attention**: tokens exchange information.
3. **Residual add.**
4. **Layer norm.**
5. **MLP**: a two-layer feed-forward network, usually $d \to 4d \to d$, applied
   to each token *independently*.
6. **Residual add.**

Almost all parameters and most FLOPs live in the MLP and the attention
projections. Attention is the only operation that mixes information *across*
positions, which is why sequence length hits it quadratically.

### 1.3 Attention, in full

For one head of dimension $d_h$, with input $X \in \mathbb{R}^{n \times d}$:

$$
Q = XW_Q,\quad K = XW_K,\quad V = XW_V,\qquad W_Q,W_K,W_V \in \mathbb{R}^{d \times d_h}
$$

$$
A = \mathrm{softmax}\!\left(\frac{QK^\top}{\sqrt{d_h}} + M\right),\qquad
O = AV
$$

$A \in \mathbb{R}^{n \times n}$ is the attention matrix. Row $i$ is a
probability distribution over keys: $A_{ij} \ge 0$, $\sum_j A_{ij} = 1$. $M$ is
a mask: $-\infty$ where a comparison is forbidden. For a decoder-only LLM the
**causal mask** sets $M_{ij} = -\infty$ for $j > i$, so token $i$ can only look
backwards.

Multi-head attention runs $h$ such heads in parallel and concatenates:

$$
\mathrm{MHA}(X) = \mathrm{Concat}(O_1, \dots, O_h)\,W_O
$$

Two much cheaper variants matter for the rest of this document:

- **MQA** (multi-query, 2019): all heads share one $K,V$. Shrinks the KV cache
  by $h\times$.
- **GQA** (grouped-query, 2023): $h_{kv} < h$ key/value heads, each shared by
  $h/h_{kv}$ query heads. Standard in current open models (Llama 3: 8 KV heads
  for 32 query heads).

Also relevant: **MLA** (multi-head latent attention, DeepSeek-V2), which
compresses K/V into a low-rank latent instead of caching full per-head tensors.
It is an orthogonal compression axis to sparsity and composes with it.

### 1.4 What the model is trained to do

A decoder-only LLM is trained on one objective: predict the next token.

$$
\mathcal{L} = -\frac{1}{n}\sum_{i=1}^{n} \log p_\theta(x_i \mid x_{\lt i})
$$

Everything else — instruction tuning, RLHF, reasoning traces — is layered on
top of that. The consequence for us: **every training token sees a
lower-triangular attention matrix**, and every generated token must attend to
everything before it. Sequence length is not an input detail; it is the axis
that the architecture scales worst along.

## 2. Prefill, decode, and the KV cache

Inference has two phases with completely different bottlenecks.

**Prefill**: the whole prompt is processed at once, as one big matrix multiply.
All $n$ queries are computed in parallel, and the full $n \times n$ score
matrix (or its causal half) is materialized inside the kernel. This is
compute-bound: FLOPS are the limit.

**Decode**: tokens are generated one at a time. For each new token, the model
needs the $K$ and $V$ vectors of *all previous tokens*. Recomputing them would
be quadratic per step, so they are cached: the **KV cache**.

For a model with $L$ layers, $h_{kv}$ KV heads, head dimension $d_h$, in
$b$ bytes per element, the cache size is:

$$
\text{bytes} = 2 \cdot L \cdot h_{kv} \cdot d_h \cdot n \cdot b
$$

For Llama-3-8B ($L=32$, $h_{kv}=8$, $d_h=128$, fp16) at $n = 131{,}072$:
**16 GiB for a single sequence** `[computed]`. That is the entire memory of a
consumer GPU, for one context, before weights.

Decode is **memory-bandwidth-bound**. Producing one token requires streaming
the whole cache through the SMs; the math per byte is tiny. On an H100
(≈989 TFLOP/s fp16, ≈3.35 TB/s), the ridge point is ≈295 FLOP/byte. Dense
decode attention achieves about **1 FLOP/byte** `[computed]` — roughly 300×
below the point where the GPU is compute-limited. This single fact explains
most of the 2023–2026 literature: at decode time, *the win is bytes not
FLOPs*.

| Phase | Shape of the work | Bottleneck | What helps |
|---|---|---|---|
| Prefill | $n$ queries × $n$ keys, one pass | FLOPS | fewer comparisons (sparsity), faster kernels, lower precision |
| Decode | 1 query × $n$ cached keys, per step | HBM bandwidth | read fewer bytes (evict/select), smaller cache (GQA/MLA), more concurrency |

## 3. A short history of LLMs

Sparse attention has been invented twice, for two different reasons. The
timeline is worth internalizing because the 2019 version and the 2025 version
are solving different problems.

| Year | Milestone | Consequence for attention |
|---|---|---|
| 2014 | Bahdanau et al., additive attention for MT | attention as an alignment mechanism between two sequences |
| 2017 | **Transformer** (Vaswani et al.) | attention replaces recurrence; training parallelizes over positions |
| 2018 | GPT-1, BERT, ELMo | pretrain-then-finetune becomes the recipe; BERT shows bidirectional attention |
| 2019 | GPT-2; **Sparse Transformer**; Blockwise; MQA | first quadratic-cost workarounds; 1K-token contexts |
| 2020 | GPT-3 (175B); Kaplan scaling laws; Longformer, BigBird, Reformer, ETC | "scale wins"; sparse attention wave #1, driven by 16 GB GPUs |
| 2021 | Routing Transformer; RoPE; ALiBi; Codex | position schemes that extrapolate; clustering-based sparsity |
| 2022 | Chinchilla; InstructGPT; **FlashAttention**; ChatGPT | exact fused attention beats approximate patterns on real hardware |
| 2023 | GPT-4; Llama/2; "Lost in the Middle"; StreamingLLM; H2O | long-context *quality* problems surface; inference-time KV sparsity begins |
| 2024 | Gemini 1.5 (1M); Claude 3 (200K); Llama 3.1 (128K); MInference, Quest, SnapKV; Qwen2.5-1M | 128K–1M becomes a product feature; sparse decoding enters serving stacks |
| 2025 | Reasoning models; **NSA**, **MoBA**, DeepSeek DSA; Gemma 3 and gpt-oss sliding-window layers | sparsity returns as a *trained* architectural choice |
| 2026 | Large-scale evaluation (Sparse Frontier, ACL 2026); hybrid local/global defaults | the field learns which sparsity actually holds up |

### Era 1 (2017–2019): architecture

The Transformer's selling point was parallel training over sequence positions.
Attention cost $O(n^2)$, but $n$ was 512–1,024 tokens, so that was irrelevant.
The problems were translation and language modeling, not 100K-token documents.

### Era 2 (2020–2021): scale

GPT-3 (2020) and the Kaplan scaling laws made one thing clear: loss falls
predictably with parameters, data, and compute. Context length was not part of
that recipe — GPT-3 used 2,048 tokens. Meanwhile attention's quadratic term
made long sequences impossible to *train* on 16 GB V100s, which produced a
wave of pattern-based sparse attention (Section 9.1). The theoretical wins were
real; the wall-clock wins mostly were not, because dense kernels were already
running at high hardware utilization and the sparse ones were not.

### Era 3 (2022–2023): alignment and the first real long contexts

InstructGPT and ChatGPT moved the product bottleneck from pretraining to
post-training. FlashAttention (2022) made *exact* attention IO-aware and
2–4× faster, undercutting the case for approximate patterns on short and
medium contexts. Context windows grew anyway: 4K → 32K → 100K → 200K, driven
by retrieval, codebases, and document QA.

Two negative results landed in the same period:

- **"Lost in the Middle"** (Liu et al., 2023): models retrieve information at
  the start and end of a long context far better than in the middle. Longer
  context is not uniformly better context.
- Long-context benchmarks such as RULER (2024) showed that models advertised
  at 128K degrade well before 128K on multi-hop and aggregation tasks.

### Era 4 (2024–2026): long context as a product, sparsity as an architecture

Three things changed the economics:

1. **Serving at 128K–1M is dominated by attention**, especially during decode.
   A 128K context at batch size 1 is bandwidth-starved no matter how fast the
   tensor cores are.
2. **Reasoning models generate long outputs.** Chain-of-thought turns a
   prefill-heavy workload into a decode-heavy one: thousands of generated
   tokens, each reading a growing KV cache.
3. **Agentic loops re-read context constantly.** Tool output, files, and
   conversation history accumulate; the cache is the working set.

The result: sparsity came back, but as *trained* sparsity inside the model
(DeepSeek NSA, Moonshot MoBA, DeepSeek-V3.2's lightning indexer; sliding-window
layers in Gemma 3 and OpenAI's gpt-oss) plus *serving-time* sparsity on top of
dense checkpoints (MInference, Quest, SnapKV, deployed in vLLM). The 2025–2026
literature is largely about which of these survives contact with real tasks.

## 4. Why long context is expensive

Three separate curves, often conflated:

**Training.** Compute is ≈ $6ND$ FLOPs for $N$ parameters and $D$ training
tokens. Attention adds $4Ln^2d$ per sequence (query–key and
attention–value products, both $2n^2d$ per layer, ignoring the causal
factor-of-2 saving). At $n=8{,}192$, an 8B model spends about **27%** of
forward FLOPs on attention; at $n=131{,}072$, the attention term is **≈4.3×
the rest of the forward pass** `[computed]` ($L=32$, $d=4096$, $P=8$B). The
crossover is a property of the model, not a universal constant, but the trend
is: attention becomes the dominant term somewhere in the tens of thousands of
tokens.

**Prefill latency.** Time-to-first-token scales quadratically. This is what
users feel when pasting a 200-page PDF.

**Decode bandwidth.** The cache grows linearly and is re-read every step. Even
at 1 FLOP/byte, a 16 GiB cache at 3 TB/s gives a hard floor of ≈5 ms per token
if you must touch all of it `[computed]`. That is 200 tok/s *maximum* from
bandwidth alone, before any compute, at batch size 1.

Quadratic compute and linear-but-re-read memory are different problems with
different fixes, and sparse attention is used for both. Confusing them is the
most common source of bad engineering decisions in this area.

## 5. The space of fixes

Sparse attention is one point in a larger design space. It is worth knowing
what else is on the shelf, because the right answer is often a combination.

| Approach | What it changes | Cost scaling | Weakness |
|---|---|---|---|
| **Sparse attention** | which query–key pairs are computed | $O(nk)$ | pattern must match the task; irregular access |
| Sliding-window layers | local attention only | $O(nw)$ | no long-range information across layers unless interleaved with global |
| Linear attention | replace softmax with a kernel feature map | $O(n)$ | different function; weaker recall in practice |
| State-space models (Mamba, hybrids) | replace attention with recurrence | $O(n)$ | not attention; hybrid stacks keep a few attention layers |
| Low-rank (Linformer) | project keys/values to rank $r$ | $O(nr)$ | quality loss at long $n$; approximation |
| KV cache compression (GQA, MLA, quantization) | store fewer/smaller bytes | memory only | does not reduce comparisons, only bytes |
| KV eviction / selection | read fewer cache entries at decode | $O(nk)$ decode | irreversible loss; quality depends on task |
| Exact fast kernels (FlashAttention) | same math, better memory traffic | $O(n^2)$ FLOPs, $O(n)$ HBM | no asymptotic win; still quadratic compute |
| Retrieval (RAG) | don't put it in context | $O(\log N)$ lookup | retrieval errors; no reasoning over the whole corpus |
| Prompt/context compression | summarize or prune tokens | reduces $n$ | information loss before the model sees it |

A useful mental model: **sparse attention reduces the number of pairs; GQA/MLA
reduce the bytes per pair; FlashAttention reduces the traffic per pair.** They
compose multiplicatively.

---

# Part II — Sparse attention

## 6. Definition and cost model

Dense causal attention computes, for every query $i$, a distribution over all
keys $j \le i$. Sparse attention picks a set

$$
S(i) \subseteq \{j : j \le i\}, \qquad |S(i)| = k_i \ll i
$$

and computes

$$
O_i = \sum_{j \in S(i)}
\frac{\exp\!\left(q_i^\top k_j / \sqrt{d_h}\right)}
     {\sum_{j' \in S(i)} \exp\!\left(q_i^\top k_{j'} / \sqrt{d_h}\right)}\, v_j
$$

Two things to notice:

1. **The softmax is renormalized over $S(i)$.** The result is not dense
   attention with zeros; it is a different function. If $S(i)$ excludes a key
   with large score, that mass is redistributed, not dropped.
2. **The pattern is per query.** $S(i)$ can be fixed (a window), input-dependent
   (top-$k$ by score), or structural (a block of queries shares a selection).

**Sparsity** is usually reported as $s = 1 - \mathbb{E}[k_i]/n$: the fraction
of query–key interactions *not* computed. A "90% sparse" model still computes
10% of the matrix — at 128K that is 1.7 billion score entries per layer, not
zero.

**Cost.** Dense causal attention per layer costs $4n^2d$ FLOPs (two matmuls,
each $2n^2d$). Sparse costs $4nk d$ plus the cost of *deciding* $S(i)$. The
decision problem is where implementations live or die:

- fixed patterns: $O(1)$ decision, no adaptivity;
- top-$k$ over exact scores: $O(n^2)$ decision — saves nothing;
- cheap proxies (pooled keys, low-rank indexer, page norms): $O(n \cdot \text{proxy})$,
  which is the real design surface.

### Sparse vs. approximating dense

Keep two questions apart:

- *Does the model define attention over a subset?* Then you have a different
  architecture. You train it and evaluate the model, not the approximation
  error.
- *Does a dense model's attention get approximated at inference?* Then quality
  is measured against the dense model on tasks, and the approximation error
  matters.

Most confusion in the literature comes from mixing these. A sliding-window
model is not "dense attention with 90% of the matrix thrown away"; it never had
the long-range edges. Conversely, H2O on Llama is an approximation and can be
scored by how much attention mass it retains.

### What "dense checkpoint" means here

"Dense" is overloaded in LLM writing. In this document it means **full
attention**: every query scores every allowed key, and no sparse pattern is
baked into the weights. It does *not* mean:

- *dense weights* (as opposed to quantized or pruned) — orthogonal, and
  compatible with attention sparsity;
- *dense model* (as opposed to a mixture-of-experts model) — there "sparse"
  describes which parameters fire per token, not which keys are attended to.

The distinction matters because **training-free sparsity operates on the
attention distribution the dense checkpoint already learned**. It can preserve
mass that exists; it cannot create long-range behavior the model never had.
That is why the 2023–2026 methods are pattern *discovery* rather than pattern
*design*: profile the checkpoint, find the heads that are already local or
already sparse, and skip what they do not use. It also fixes the quality
reference — approximation error is measured against this checkpoint's outputs
— and means that changing the base model invalidates the calibration, because
head patterns, sink positions, and per-layer budgets are properties of
specific weights.

The practical consequence for Section 13: a "dense checkpoint" row in the
design table is a statement about *what you are allowed to change*. You can
change the kernel and the selection policy; you cannot change the function
without retraining, which is exactly what separates that row from the native
sparsity row.

## 7. A gallery of patterns

Masks below are causal: row = query, column = key, `█` = computed, `·` = skipped.

**Dense causal** — $O(n^2)$:

```
█ · · · · · · ·
█ █ · · · · · ·
█ █ █ · · · · ·
█ █ █ █ · · · ·
█ █ █ █ █ · · ·
█ █ █ █ █ █ · ·
█ █ █ █ █ █ █ ·
█ █ █ █ █ █ █ █
```

**Sliding window, $w=2$** — $O(nw)$; what Mistral-style and Gemma-style local
layers do. Cheap, hardware-friendly, cannot retrieve anything older than $w$
per layer.

```
█ █ █ · · · · ·
█ █ █ █ · · · ·
█ █ █ █ █ · · ·
· █ █ █ █ █ · ·
· · █ █ █ █ █ ·
· · · █ █ █ █ █
· · · · █ █ █ █
· · · · · █ █ █
```

**Global + window** — $O(nw + gn)$; Longformer, BigBird, ETC, attention sinks.
The first $g$ columns are always visible.

```
█ █ · · · · · ·
█ █ · · · · · ·
█ █ █ · · · · ·
█ █ █ █ █ █ · ·
█ █ █ █ █ █ █ ·
█ █ · █ █ █ █ █
█ █ · · █ █ █ █
█ █ · · · █ █ █
```

**Block-sparse (2×2 blocks here, 64–128 real)** — what kernels can actually
accelerate. Diagonal blocks plus a globally visible first block column:

```
█ █ · · · · · ·
█ █ · · · · · ·
█ █ █ █ · · · ·
█ █ █ █ · · · ·
█ █ · · █ █ · ·
█ █ · · █ █ · ·
█ █ · · · · █ █
█ █ · · · · █ █
```

**Two more shapes seen in production** (not drawn): *vertical–slash* — a set of
columns shared by all queries plus diagonals at offsets (MInference); and
*page selection* — the KV cache is split into contiguous pages and each decoded
query reads a top-$k$ subset (Quest). The second has no meaningful prefill
pattern; it exists only at decode.

## 8. Taxonomy

The most useful decomposition is the one used by the Sparse Frontier evaluation
(Nawrot et al., 2026): four axes, independent of the method's name.

| Axis | Options | Examples |
|---|---|---|
| **Unit** | token, page/block, column (vertical), diagonal (slash), window | Quest (pages), MInference (verticals + slashes), BigBird (window + global + random) |
| **Importance** | fixed / calibrated / content-aware | StreamingLLM (fixed), SnapKV (content), NSA (learned indexer) |
| **Budget** | uniform, per-layer, per-head, threshold on attention mass | Block-Sparse (uniform), Ada-KV (per-head), FlexPrefill (threshold) |
| **KV management** | none (recompute/keep all), eviction, full-cache selection | MInference (none), H2O (eviction), Quest (selection over full cache) |

Two further distinctions cut across all of them:

- **Trainable vs. training-free.** Trainable patterns are part of the model and
  the loss can adapt to them. Training-free patterns must work on a dense
  checkpoint, so they are restricted to what the pretrained attention already
  does — which, empirically, is "attend to the recent window and a few sink
  tokens".
- **Prefill vs. decode.** Prefill has $n$ queries and needs a pattern that is
  efficient to *estimate* for all of them at once. Decode has one query and can
  afford a more expensive per-step decision, but pays for it on every token.
  Methods that are excellent at one phase are routinely mediocre at the other.

### Static vs. dynamic

Static patterns (window, strided, block-diagonal) cost nothing to compute and
generalize badly when the task needs a different shape. Dynamic patterns
(top-$k$, clustering, learned routing) adapt but add an estimator whose cost
is easy to underestimate. The estimator must be *sub-quadratic and cheap
relative to the attention it replaces*, or the arithmetic is a wash:

$$
\text{net speedup} \approx \frac{1}{r + c}
$$

where $r$ is the retained fraction of attention work and $c$ is the estimator's
cost as a fraction of dense attention. At $r=0.1$, an estimator costing 20% of
dense attention halves your speedup before any kernel inefficiency. This is the
single most common accounting error in blog-post benchmarks.

## 9. Chronology of methods

### 9.1 The training-efficiency wave (2019–2021)

Hardware context: 16 GB V100s, no FlashAttention, no GQA. Long sequences did
not fit, so the goal was to make *training* cheaper.

**Sparse Transformer** (Child et al., 2019) introduced factored patterns:
attend along a strided/dilated grid (every $s$-th token) plus local neighbors,
giving an $O(n\sqrt{n})$ receptive field. Two attention stacks with different
factorizations recover full connectivity in two layers. This is the paper that
established the vocabulary — strided, fixed, learned — and the
"pattern-as-architecture" framing.

**Blockwise** (Qiu et al., 2019) made sparsity block-aligned for GPU efficiency:
attention is computed on $b \times b$ tiles, with a block-sparse layout. The
lesson — align the pattern to what the hardware can skip — has been rediscovered
every two years since.

**ETC** (Ainslie et al., 2020) added global tokens that attend to and are
attended by everything. The global-token idea is the cheapest known fix for the
information loss of local patterns, and it survives today as attention sinks.

**Longformer** (Beltagy et al., 2020) combined a sliding window with task-
specific global tokens, plus dilated windows in deeper layers. Cost $O(nw)$.
It was the default long-document encoder for a while and is still the clearest
statement of the design: local for most tokens, global for a few.

**BigBird** (Zaheer et al., 2020) added random edges to window + global, proved
Turing-completeness/universal-approximation properties for the resulting
sparse graph, and achieved $O(n)$ with linear projections. The random component
is theoretically appealing and practically awkward: it destroys block
regularity unless you fix a random seed and pretrain the pattern into the
kernel.

**Reformer** (Kitaev et al., 2020) took a different route: locality-sensitive
hashing to bucket similar queries and keys, then attend within buckets. Cost
$O(n \log n)$. Constraints: queries and keys must be identical (shared
projection), buckets must be balanced, and sorting dominates at moderate $n$.
It is the canonical content-based method and also the canonical example of an
estimator whose overhead erases the asymptotic win.

**Routing Transformer** (Roy et al., 2021) clustered queries and keys with
online k-means and attended within clusters, $O(n^{1.5})$. Same story: elegant,
sensitive to cluster quality, hard to make fast.

Why the wave receded: FlashAttention (2022) made dense attention 2–4× faster
with exact math, while the sparse methods were paying index, sort, and
irregular-access overheads. A 30% FLOP reduction that runs at 15% of peak is
slower than dense at 60% of peak. The field learned to ask "faster than what,
on which kernel" instead of "lower complexity".

### 9.2 The inference wave (2023–2024)

Context: 128K–1M windows, decode-bound serving, and dense checkpoints that
people wanted to run longer without retraining.

**StreamingLLM** (Xiao et al., 2023) observed **attention sinks**: the first few
tokens absorb a large fraction of attention mass regardless of content, because
softmax needs somewhere to put unused probability. Keeping four sink tokens
plus a sliding window allows unbounded streaming with a bounded cache, and the
paper reports large speedups over recomputation-based sliding windows. The
failure mode is equally important: evict the sinks and the model degrades
sharply.

**H2O** (Zhang et al., 2023) identified "heavy hitter" tokens from accumulated
attention scores and kept them, evicting the rest — a fixed-size KV cache with
content-based retention.

**SnapKV** (Li et al., 2024) selects KV positions using the last window of
queries during prefill, on the observation that recent queries are a good proxy
for what future queries will need. Compression is applied once, at the end of
prefill.

**InfLLM** (Xiao et al., 2024) and **Quest** (Tang et al., 2024) keep the full
cache but *select* pages per step. Quest's contribution is the cheap estimator:
per-page metadata (min/max key per dimension) gives an upper bound on the
query–page score, so top-$k$ page selection costs a fraction of reading the
pages. This is the decode-time design that the 2026 evaluation found most
robust.

**MInference** (Jiang et al., 2024) attacked prefill instead: profile a dense
model offline, classify heads into patterns (A-shape for sink+local, vertical–
slash for column+diagonal structure, block-sparse), and build sparse prefill
kernels per pattern. Reported up to 10× prefill speedup at 1M tokens on an
A100. Vertical–slash later shipped in Qwen2.5-1M's serving path.

The through-line: these methods work because dense pretrained attention is
*already* sparse in practice — most of its mass is on a local window plus a few
outliers. You are not inventing a pattern; you are discovering one.

### 9.3 Native sparsity (2025–2026)

The current wave makes sparsity a trained part of the architecture, with kernels
designed alongside it.

**NSA** (Yuan et al., 2025, DeepSeek) uses three parallel branches per query:
coarse *compressed* attention over pooled blocks (cheap global view), *selected*
attention over top-$n$ fine-grained blocks chosen by a learned/score-based
index, and a *sliding window* for local precision. All three are summed with
learned gates, and the whole thing is trained end-to-end. The paper emphasizes
arithmetic-intensity balancing: block sizes are chosen so the kernel stays
compute-bound on modern GPUs. Reported speedups at 64K: 11.6× decode, 9.0×
forward, 6.0× backward, with quality matching or exceeding full attention in
their pretraining comparison.

**MoBA** (Lu et al., 2025, Moonshot) applies Mixture-of-Experts routing to
context blocks: partition the context into blocks, score blocks per query with
a small gate, and attend only to the top-$k$ blocks. Because selection is
block-granular and gated, it maps onto standard grouped-GEMM kernels. Evaluated
on 1M-token contexts with RULER; the selling point is that sparsity is learned
rather than calibrated, so it transfers across tasks better than fixed patterns.

**DeepSeek Sparse Attention (DSA)**, shipped in DeepSeek-V3.2-Exp, uses a
"lightning indexer": a small, FP8, low-head-dim scoring network that computes a
cheap per-token relevance score for every query–token pair, followed by top-$k$
selection (2,048 tokens per query) and a purpose-built sparse kernel. Note the
honest accounting in the Sparse Frontier paper: the indexer is still
$O(n^2 d_{\text{index}})$ — it is quadratic, just over a much smaller
dimension — and the win comes from pairing it with a token-level kernel that
actually skips work. Neither half is sufficient alone.

**Sliding-window layers in production models.** Gemma 3 interleaves five local
layers (window 1,024) with one global layer; gpt-oss alternates 128-token
sliding-window layers with full-attention layers. This is the least glamorous
and most widely deployed form of sparsity: a fixed budget, chosen at
pretraining, that bounds the attention cost of most layers.

The 2026 evaluation literature (Nawrot et al., ACL 2026 Findings) is the first
large-scale attempt to say which of these actually pays off. Its headline
results are in Section 11.

## 10. Kernels: why declared sparsity is not speed

This is the section most explanations skip, and it is the one that determines
whether your change does anything.

### 10.1 Three ways to implement a pattern

**1. Masking.** Build the $n \times n$ score matrix, add $-\infty$ to excluded
entries, run softmax. Correct, simple, and *useless for speed*: the matmul and
the memory traffic are both still $O(n^2)$. It is the right tool for a 4K-token
prototype and the wrong tool for 128K.

**2. Gather/index.** Materialize only the selected keys per query and run a
batched matmul over the gathered tensor.

```python
# sliding window, reference implementation (not fast)
W = 256
idx = torch.arange(n, device=q.device)
offs = torch.arange(-W, W + 1, device=q.device)
gather = idx[:, None] + offs[None, :]          # (n, 2W+1)
valid = (gather >= 0) & (gather < n)
gather = gather.clamp(0, n - 1)

k_win = k[:, :, gather]                        # (B, H, n, 2W+1, d)
v_win = v[:, :, gather]
scores = (q.unsqueeze(-2) * k_win).sum(-1) / math.sqrt(d)
scores = scores.masked_fill(~valid, float("-inf"))
out = torch.softmax(scores, -1) @ v_win
```

This has $O(nw)$ memory and FLOPs but produces a $(n, 2w+1, d)$ intermediate
with poor coalescing. Good for correctness checks, bad for throughput.

**3. Block-sparse fused kernel.** Quantize the pattern to tiles (64–256
tokens), load only selected K/V tiles into SRAM, accumulate, skip the rest.
This is the only approach that reliably beats dense FlashAttention, because it
preserves matmul shapes and memory coalescing.

```python
# conceptual FlexAttention use (mask-based, fused, no n^2 materialization)
def causal_window(b, h, q_idx, kv_idx):
    return (kv_idx <= q_idx) & ((q_idx - kv_idx) <= 256)

block_mask = create_block_mask(causal_window, B=None, H=None,
                               Q_LEN=n, KV_LEN=n, device="cuda")
out = flex_attention(q, k, v, block_mask=block_mask)
```

FlexAttention (PyTorch) compiles mask functions into fused kernels and skips
whole blocks that are fully masked; it is the sane default for research and
small-scale serving. Exact API details vary by PyTorch version.

### 10.2 Arithmetic intensity decides everything

A GPU's peak FLOPS are only reachable when enough arithmetic is done per byte
fetched. The ratio that matters:

$$
\text{intensity} = \frac{\text{FLOPs}}{\text{bytes moved}}
$$

Dense decode attention: 1 FLOP/byte (Section 2) — two orders of magnitude below
the H100 ridge point. Block-sparse attention with block size $B$:

$$
\text{intensity} = \frac{2B}{b}\ \text{FLOP/byte}
$$

For fp16 ($b=2$), that is $B$ FLOP/byte. With $B=64$ you get 64; with $B=128$,
128; with $B=256$, 256 — roughly the ridge point. **Block size is not a tuning
knob; it is the thing that determines whether the kernel can approach peak.**
This is why `64×64` and `128×128` appear in every paper's implementation
section, and why fine-grained token selection is theoretically nicer and
practically slower.

The estimator has the same problem. Per-query top-$k$ over 128K keys costs a
full pass over scores unless it is approximated; that pass is quadratic. The
workarounds are all in the literature: pool keys into blocks (MInference,
Quest), use a low-dimensional indexer (DSA), or restrict selection to a window
(SnapKV). None of them is free.

### 10.3 Amdahl's law applies

Sparse attention only removes attention work. If attention is 30% of prefill
time, the ceiling is 3.3× no matter how sparse you get. At 128K it can be 70%+
of prefill; at 8K it is often ~25%. This is why the same method looks
transformative in one benchmark and pointless in another, and why hybrid
architectures (local layers + a few global layers) often beat uniformly sparse
ones: they remove the work where it is concentrated and keep the exact path
where it is cheap.

## 11. What the measurements say

The Sparse Frontier study (Nawrot et al., ACL 2026 Findings) is the most
carefully controlled public comparison of *training-free* sparse attention to
date: six methods, Qwen 2.5 / Llama 3.1 / Gemma 3 (4B–72B), 16K–128K tokens,
sparsity up to 0.95, nine tasks, with harmonized implementations.

Findings worth carrying into design reviews:

1. **Iso-cost, sparse wins.** At equal prefill FLOPs or decode memory traffic,
   a larger sparse model beats a smaller dense one. Sparsity improves the
   Pareto frontier rather than trading along it.
2. **Prefill is the hard phase.** No training-free method paired a cheap,
   fine-grained importance estimator with a kernel that converted the resulting
   sparsity into wall-clock gains. In practice you choose between global
   (vertical) selection and block-to-block selection, and neither generalizes
   across all tasks.
3. **Decode is easier and more forgiving.** With one query per step,
   token-to-page selection (Quest-style) is cheap, generalizes better, and
   tolerates higher sparsity.
4. **Longer sequences tolerate more sparsity.** Accuracy at a fixed budget
   improves as $n$ grows, which means fixed-budget production configurations
   are leaving quality on the table; the budget should scale with $n$.
5. **Reported sparsity is not achieved speed.** The paper is explicit that
   realized gains depend on kernel efficiency, and that the estimator's cost
   belongs in the accounting.

Complementary results from the trained side: NSA reports quality parity with
full attention at 64K while being several times faster in all three phases;
MoBA reports strong 1M-token results with block-gated selection; Gemma 3 and
gpt-oss ship interleaved local/global layers and are competitive at their size.
The pattern across all of it: **sparsity that is trained and block-aligned
works; sparsity that is declared and masked does not.**

Caveat on benchmarks: needle-in-a-haystack and RULER-style synthetic tasks
overstate how well sparse patterns do on real multi-hop and aggregation work.
The 2026 study deliberately includes story-based tracking and aggregation tasks
because synthetic retrieval saturates. Evaluate on your workload.

## 12. Failure modes

- **Evicting attention sinks.** StreamingLLM's four-token prefix is not
  folklore; removing it breaks the model. Any cache policy that can drop the
  first tokens must special-case them.
- **Assuming masking saves time.** It does not. Measure FLOPs and wall-clock,
  not the config flag.
- **Fine-grained selection with a block kernel.** The kernel computes whole
  tiles anyway, so you pay dense cost and get sparse accuracy.
- **Budget set once, applied everywhere.** Heads differ: some are local,
  some retrieve globally, some are nearly uniform. Uniform budgets waste
  capacity on local heads and starve retrieval heads. Per-head and per-layer
  allocation is where most of the remaining quality is.
- **Ignoring the estimator.** A top-$k$ pass over 128K scores costs more than
  the attention it replaces. If the indexer is not sub-quadratic in a smaller
  dimension, nothing improves.
- **Positional mismatch.** With RoPE, selected keys keep their original
  positions, which is correct; but methods that renumber or compress positions
  (some token-merging schemes) change the function being computed. Rotary
  phase is not invariant to reordering.
- **Irreversible eviction.** H2O/SnapKV-style methods discard KV entries
  permanently; a later query that needs an evicted token cannot recover it.
  Selection-over-full-cache (Quest) keeps the option to be wrong differently.
- **Task mismatch.** A local-window model cannot do exact retrieval at 100K
  no matter how well it does on perplexity. If the task is "find the clause on
  page 400", the answer is usually retrieval or a global-token path, not a
  wider window.
- **Confusing prefill and decode gains.** A 10× prefill speedup does nothing
  for a chat workload that is 95% decode. Profile the phase mix first.
- **Batch-size effects.** At large batch, decode becomes compute-bound again
  (more queries per step amortize the cache read). Sparsity that wins at batch
  1 can lose at batch 64 if the kernel is less efficient. `[inference]` — this
  follows from the roofline argument, and is worth measuring per deployment.

## 13. Choosing a design

Start from the workload, not the paper.

| Situation | Reasonable default | Why |
|---|---|---|
| 8K–32K, quality-critical, training budget | dense + FlashAttention, GQA | attention is not the bottleneck yet |
| 32K–128K, pretraining from scratch | interleaved local/global layers (5:1 or 1:1) | fixed, cheap, no estimator, proven in Gemma 3/gpt-oss |
| 128K–1M, pretraining, attention-dominated | native block-sparse (NSA/MoBA-class) | learned selection + hardware-aligned blocks |
| Dense checkpoint, need 1M prefill now | MInference-style pattern discovery + vertical–slash | no retraining; 64-token block granularity |
| Dense checkpoint, long decode | page selection (Quest) with cheap metadata | decode tolerates sparsity; estimator is affordable |
| Streaming chat, unbounded input | sinks + sliding window, bounded cache | no growth, no eviction surprises |
| Memory-constrained serving | GQA/MLA + KV quantization first, eviction second | bytes before comparisons |
| Exact retrieval over a large corpus | retrieval, not attention sparsity | sparsity is not a search index |

**Sizing the budget.** Do not pick a fixed fraction. Two rules that follow from
the measurements:

1. Budget per head, not per model. Measure each head's attention entropy and
   mass distribution on real data; give retrieval heads more.
2. Let the budget grow with $n$ (roughly $k \propto \sqrt{n}$ for prefill
   kernels, or a fixed page count for decode) so that sparsity increases only
   as fast as the sequence does.

**Deployment checklist.** Work through these in order. The recall metric
referenced below is

$$
\mathrm{recall} = \frac{\sum_i \sum_{j \in S(i)} A_{ij}}{\sum_i \sum_j A_{ij}}
$$

the fraction of the dense model's attention mass that the selected pattern
retains.

- [ ] Profile the phase mix (prefill vs decode) on the actual workload.
- [ ] Compute the attention share of total time; if it is under ~20%, stop.
- [ ] Pick block granularity ≥ 64, ideally 128, aligned to the kernel.
- [ ] Measure achieved FLOPs/bytes with a profiler, not the config.
- [ ] Check attention-mass recall on real inputs, per head.
- [ ] Evaluate on aggregation and multi-hop tasks, not just NIAH.
- [ ] Sweep sparsity at your target $n$; do not reuse a 4K-derived setting.
- [ ] Verify batch-size behavior at production concurrency.
- [ ] Keep one dense layer (or a global path) as insurance.

## 14. Reference implementations and checks

### 14.1 Verify the pattern before optimizing it

```python
import torch, math

def dense_attention(q, k, v, causal=True):
    # q, k, v: (B, H, n, d)
    s = q @ k.transpose(-1, -2) / math.sqrt(q.size(-1))
    if causal:
        n = q.size(-2)
        s = s.masked_fill(torch.triu(torch.ones(n, n, dtype=torch.bool,
                                                 device=q.device), 1), float("-inf"))
    return torch.softmax(s, -1) @ v

def attention_mass(A, keep):
    # A: (B, H, n, n) row-stochastic; keep: bool mask
    return (A * keep).sum() / A.sum()
```

A correct sparse implementation should match `dense_attention` when the mask is
all-ones, and should report the mass recall above. Divergence on the all-ones
case is a bug; divergence under a real mask is expected and is the thing you
are trading.

### 14.2 Cost sanity check

```python
def kv_gib(layers, kv_heads, head_dim, seq, bytes_per=2):
    return 2 * layers * kv_heads * head_dim * seq * bytes_per / 2**30

kv_gib(32, 8, 128, 131_072)      # 16.0 GiB for Llama-3-8B at 128K
```

If the cache does not fit with room for weights and activations, no amount of
attention sparsity fixes the deployment; you need GQA/MLA, quantization,
offloading, or a shorter context.

### 14.3 Minimal block-sparse mask construction

```python
def block_mask(n, block, keep_blocks):
    """keep_blocks: set of (q_block, kv_block) index pairs."""
    m = torch.zeros(n, n, dtype=torch.bool)
    for qb, kb in keep_blocks:
        m[qb*block:(qb+1)*block, kb*block:(kb+1)*block] = True
    return m
```

`keep_blocks` is what a kernel consumes; the dense bool matrix is only for
testing. In production the pattern is passed as block indices (or a compressed
bitmap), never as an $n \times n$ tensor.

## 15. Glossary

Terms as used in this document. Where the field uses a word inconsistently,
the entry says so; several of the worst confusions (dense, sparse, block) are
called out explicitly.

### 15.1 Symbols

| Symbol | Meaning |
|---|---|
| $n$ | sequence length, in tokens |
| $d$ | model width (residual stream dimension) |
| $d_h$ | per-head dimension |
| $L$ | number of transformer layers |
| $h$ | number of query heads |
| $h_{kv}$ | number of key/value heads (MQA/GQA) |
| $w$ | sliding-window width |
| $k_i$ | keys retained by query $i$ |
| $S(i)$ | retained key set for query $i$ |
| $s$ | sparsity, $1 - \mathbb{E}[k_i]/n$ |
| $A$ | attention matrix, rows sum to 1 |
| $B$ | block size in tokens |
| $b$ | bytes per stored element |
| $r$ | retained fraction of attention work |
| $c$ | estimator cost as a fraction of dense attention |

### 15.2 Model and architecture

**token** — The unit the model reads: a subword fragment, typically 3–4 English
characters. Context length is counted in tokens (1M tokens ≈ 750K words).

**tokenizer** — Maps text to token IDs and back. BPE, WordPiece, or
SentencePiece, fixed at pretraining time. Vocabulary 32K–256K.

**embedding** — The $V \times d$ matrix mapping token IDs to vectors; often
tied to the output projection.

**decoder-only** — Architecture of GPT/Llama-style models: every token attends
only to previous tokens. Encoder-decoder and bidirectional encoders exist;
"LLM" in this document means decoder-only.

**causal mask** — The upper-triangular $-\infty$ mask that hides future keys.
Halves the useful attention matrix; kernels exploit the fact.

**positional encoding** — How order enters a permutation-invariant operation.
RoPE rotates Q/K by position-dependent angles and yields relative positions;
ALiBi adds a distance-proportional bias to scores.

**residual stream** — The $d$-dimensional vector flowing through the model;
each block reads from it and adds its output back into it.

**layer norm** — Normalization applied per token, usually pre-norm. RMSNorm is
the cheaper variant used by most current models.

**MLP (FFN)** — Per-token feed-forward network, typically $d \to 4d \to d$.
Holds most parameters and most FLOPs, and mixes no information across positions.

**parameter** — A trained scalar. "8B model" means $8\times10^9$ parameters,
not operations per token.

**loss** — The scalar minimized during training. For an LLM it is the mean
negative log-likelihood of the next token, equivalently the cross-entropy
between the predicted distribution and the one-hot target:
$-\frac{1}{n}\sum_i \log p_\theta(x_i \mid x_{\lt i})$. Perplexity is
$e^{\text{loss}}$. Training loss and validation loss are the same quantity on
different data; neither measures long-context retrieval.

**context window** — Maximum tokens attendable in one call. Bounded by
training, positional scheme, and memory.

**scaling law** — Empirical power law relating loss to parameters, data, and
compute; the reason the field scales before it optimizes.

**Chinchilla-optimal** — Compute-optimal ratio of roughly 20 training tokens
per parameter (Hoffmann et al., 2022). Most current models deliberately
overtrain past it.

**mixture-of-experts (MoE)** — Each token is routed to $k$ of $N$ expert MLPs.
"Sparse model" there means sparse *parameter* activation; it has nothing to do
with which keys attention reads.

**checkpoint** — A saved weight set. A **dense checkpoint** has full attention
and no sparsity trained in; see Section 6.

**quantization** — Storing weights or KV in lower precision (FP8, INT8, 4-bit).
Cuts bytes and can raise throughput; does not reduce the number of comparisons.

### 15.3 Attention mechanics

**head** — One attention channel with its own $Q,K,V$ projections and dimension
$d_h$; $h$ heads run in parallel and are concatenated.

**attention score (logit)** — $q_i^\top k_j / \sqrt{d_h}$ before softmax. Large
positive means "attend here".

**attention weight** — Post-softmax entry $A_{ij}$; each row sums to 1.

**attention matrix** — The $n \times n$ table of weights. Dense, it is
quadratic in memory; sparse, it is mostly implicit and never materialized.

**attention entropy** — Entropy of a row's weight distribution. Low entropy
means focused attention (retrieval, sinks); high entropy means diffuse
attention (often local smoothing).

**local head** — Informal: a head whose mass sits on nearby tokens. Common in
lower layers and in models trained with sliding windows.

**retrieval head** — Informal: a head whose mass concentrates on a few distant,
task-relevant tokens. The empirical justification for per-head budgets.

**induction head** — A two-head circuit that recognizes a repeated prefix and
copies what followed it the previous time. Direct evidence that some attention
implements lookup rather than smoothing.

**attention sink** — Early tokens, usually the first few, that absorb large
attention mass regardless of content because softmax must place unused
probability somewhere. Removing them breaks streaming models.

**softmax renormalization** — Under sparsity the denominator ranges over
$S(i)$ only; excluded mass is redistributed. This is why sparse attention is a
different function, not dense attention with zeros.

**KV cache** — Stored keys and values for past tokens, re-read at every decode
step. Size $2 L h_{kv} d_h n b$ bytes; the decode bottleneck.

**prefill** — Processing the prompt in one parallel pass. Compute-bound, with
$O(n^2)$ attention FLOPs.

**decode** — Generating one token at a time against the cache. Bandwidth-bound,
at roughly 1 FLOP/byte for fp16 dense attention.

**MQA** — Multi-query attention: a single shared $K,V$ head. Shrinks the cache
by $h\times$; costs quality at large head counts.

**GQA** — Grouped-query attention: $h_{kv}$ KV heads shared by groups of query
heads. Cache shrinks by $h/h_{kv}$; the default in current open models.

**MLA** — Multi-head latent attention (DeepSeek-V2): cache a low-rank latent
instead of full per-head $K,V$. Orthogonal to sparsity, and composes with it.

**PagedAttention** — vLLM's cache layout: fixed-size blocks plus a block table,
like virtual memory. Removes fragmentation and makes page-granular selection
natural.

**prefix caching** — Reusing the KV of a shared prefix (system prompt, file)
across requests. Shifts the cost mix: cached prefill makes decode sparsity
relatively more valuable.

**continuous batching** — Iteration-level scheduling where requests join and
leave mid-flight. Raises effective batch size, which can make decode
compute-bound again.

### 15.4 Sparse attention

**sparse attention** — Attention restricted to $S(i)$ per query, with
$|S(i)| = k \ll n$: $O(nk)$ instead of $O(n^2)$.

**pattern** — The rule defining $S(i)$: window, block layout, columns,
diagonals, or content-dependent selection.

**fixed (static) pattern** — Same shape for every input. Zero estimation cost;
cannot adapt to the content.

**dynamic (content-aware) pattern** — Chosen per input from scores or routing.
Better quality; adds an estimator whose cost must be counted.

**sparsity ($s$)** — Fraction of query–key pairs not computed,
$s = 1 - \mathbb{E}[k_i]/n$.

**budget** — The complement of sparsity: retained fraction, or an absolute
count per query, head, or layer.

**block / page** — A contiguous run of tokens (typically 64–256) that a kernel
can skip as a unit. "Page" is the KV-cache term, "block" the attention-matrix
term; both mean the same thing to the hardware.

**sliding window (SWA)** — Each query attends to the previous $w$ tokens.
$O(nw)$; loses long-range information unless interleaved with global layers.

**dilated / strided pattern** — Attend to every $s$-th token plus neighbors;
grows the receptive field geometrically (Sparse Transformer).

**global token / vertical** — A key visible to every query. The cheapest fix
for local blindness; its trained form is an attention sink.

**slash** — A diagonal band at a fixed offset from the query, capturing
periodic structure (MInference combines slashes with verticals).

**random attention** — A fixed set of random edges added to window plus global
(BigBird). Good theory, awkward for kernels.

**LSH attention** — Hash queries and keys into buckets and attend within
buckets (Reformer). $O(n \log n)$; requires shared Q/K and balanced buckets.

**clustering attention** — Cluster queries/keys and attend within cluster
(Routing Transformer). $O(n^{1.5})$; quality depends on cluster quality.

**top-$k$ selection** — Keep the $k$ highest-scoring units per query. Exact
scoring is quadratic, so practical systems score cheap proxies instead.

**threshold selection** — Keep units until a target fraction of attention mass
(e.g. 95%) is covered; adapts the budget per head. Used by FlexPrefill and
SampleAttention.

**indexer / estimator** — The cheap scorer that chooses $S(i)$. Its cost
belongs in the accounting: net speedup $\approx 1/(r+c)$.

**eviction** — Permanently dropping KV entries (H2O, SnapKV). Irreversible: a
later query that needs an evicted token cannot get it back.

**selection** — Choosing a subset of the full cache at each step (Quest).
Keeps the option to choose differently next step; costs a metadata pass over
the cache.

**token merging** — Combining similar tokens before attention (ToMe). Reduces
$n$ but changes the representation; it is not sparsity.

**prompt compression** — Pruning or summarizing the input before the model sees
it (LLMLingua). Lossy preprocessing, not an attention mechanism.

**native (trainable) sparsity** — Pattern designed into the model and trained
end-to-end (NSA, MoBA, DSA, sliding-window layers). The function adapts to the
pattern.

**training-free sparsity** — Pattern applied to a dense checkpoint at inference
(MInference, Quest, SnapKV). Must work with attention the model already learned.

**dense checkpoint** — Full-attention weights with no sparsity trained in; the
input to, and quality reference for, training-free methods.

**hybrid local/global** — Interleaving windowed and full layers (Gemma 3 at
5:1, gpt-oss alternating). Fixed cost, no estimator, proven at scale.

**attention-mass recall** — $\sum_{i}\sum_{j \in S(i)} A_{ij} / \sum_{i}\sum_j
A_{ij}$: the fraction of dense attention mass the pattern retains. The right
first sanity metric; not the same as task accuracy.

**declared vs. achieved sparsity** — The fraction you configured versus the
fraction the kernel actually skips. They diverge whenever a mask is
materialized or a tile is computed anyway.

**iso-cost** — Comparison at equal prefill FLOPs or equal decode bytes. The
only fair way to compare a sparse 70B against a dense 8B.

**2:4 structured sparsity** — NVIDIA feature that skips two of every four
*weights* in a matmul. Unrelated to attention sparsity; a frequent source of
confusion in search results.

### 15.5 Kernels and hardware

**FLOPs / MAC** — Floating-point operations; one multiply-add is 2 FLOPs. A
"MAC" counts multiply-accumulates, so MACs are half the FLOP count.

**arithmetic intensity** — FLOPs per byte moved. Below the ridge point the
kernel is bandwidth-limited; above it, compute-limited.

**roofline / ridge point** — Performance model against intensity; the ridge is
peak FLOPs ÷ peak bandwidth (≈295 FLOP/byte for H100 fp16).

**compute-bound / memory-bound** — Which resource limits throughput. Prefill at
long $n$ is compute-bound; decode at small batch is memory-bound.

**HBM** — High-bandwidth DRAM, off-chip (3.35 TB/s on H100). Home of weights
and KV cache.

**SRAM** — On-chip memory per SM, hundreds of KB. Home of tiles during a
matmul; the reason tiling exists at all.

**tile** — A sub-block small enough for SRAM and large enough for tensor cores,
typically 64–256 tokens per side.

**fused kernel** — One kernel performing matmul, mask, softmax, and the second
matmul without writing intermediates to HBM. FlashAttention is the canonical
example.

**FlashAttention** — IO-aware exact attention: tile over K/V, track a running
max and sum (online softmax), never materialize $A$. Exact math, not sparse.

**online softmax** — Computing softmax in one streaming pass by rescaling the
running sum whenever a new maximum appears.

**block-sparse kernel** — A kernel that loads only selected tiles. The only
implementation that reliably converts sparsity into wall-clock time.

**FlexAttention** — PyTorch's mask-function-to-fused-kernel compiler; skips
fully masked blocks and is the sane default for research.

**Triton / CUTLASS** — Kernel DSL (Triton) and C++ template library (CUTLASS)
used to write production block-sparse attention.

**coalescing** — Adjacent threads accessing adjacent addresses. Irregular
gathers break it, which is why fine-grained selection loses to block selection.

**occupancy** — Active warps per SM relative to the maximum. Kernels with
variable work per block often run at low occupancy.

**tensor core** — Matrix-multiply unit requiring fixed tile shapes and low
precision. Patterns that break tile shapes cannot use it efficiently.

**FP16 / BF16 / FP8** — Numeric formats for weights, activations, and caches.
Bytes per element set both cache size and the arithmetic-intensity thresholds.

**Amdahl's law** — Speedup is capped by the fraction left unoptimized. At 30%
attention share, the prefill ceiling is 3.3×.

**TTFT** — Time to first token; dominated by prefill and queueing.

**TPOT / ITL** — Time per output token / inter-token latency; dominated by
decode bandwidth at small batch.

**throughput** — Aggregate tokens per second across the batch; the cost metric,
as opposed to latency.

**batch size** — Sequences processed together. Larger batches amortize the KV
read and can flip decode from memory- to compute-bound.

### 15.6 Evaluation

**perplexity** — $\exp$ of mean negative log-likelihood. Cheap and sensitive to
local fluency, nearly blind to long-range retrieval; necessary, not sufficient.

**NIAH** — Needle-in-a-haystack: plant a fact, ask for it. Saturates early and
overstates real long-context capability.

**RULER** — Suite with retrieval, multi-hop, aggregation, and variable tracking
at controlled lengths. Better than NIAH, still synthetic.

**lost in the middle** — Finding that models use information at the start and
end of a context better than the middle. A long window is not a usable window.

**multi-hop / aggregation** — Tasks needing several pieces of evidence, or
counting/summing across the whole context. The first tasks a sparse pattern
fails.

**Pareto frontier** — Configurations not dominated on both cost and quality.
"Sparse beats dense" is a frontier claim, not a point comparison.

## 16. References

Foundations

- D. Bahdanau, K. Cho, Y. Bengio. "Neural Machine Translation by Jointly
  Learning to Align and Translate." ICLR 2015. arXiv:1409.0473.
- A. Vaswani et al. "Attention Is All You Need." NeurIPS 2017. arXiv:1706.03762.
- A. Radford et al. "Language Models are Unsupervised Multitask Learners."
  OpenAI, 2019. (GPT-2)
- T. Brown et al. "Language Models are Few-Shot Learners." NeurIPS 2020.
  arXiv:2005.14165.
- J. Kaplan et al. "Scaling Laws for Neural Language Models." 2020.
  arXiv:2001.08361.
- J. Hoffmann et al. "Training Compute-Optimal Large Language Models."
  NeurIPS 2022. arXiv:2203.15556.
- N. Shazeer. "Fast Transformer Decoding: One Write-Head is All You Need."
  2019. arXiv:1911.02150. (MQA)
- J. Ainslie et al. "GQA: Training Generalized Multi-Query Transformer Models
  from Multi-Head Checkpoints." EMNLP 2023. arXiv:2305.13245.
- DeepSeek-AI. "DeepSeek-V2: A Strong, Economical, and Efficient
  Mixture-of-Experts Language Model." 2024. arXiv:2405.04434. (MLA)
- J. Su et al. "RoFormer: Enhanced Transformer with Rotary Position Embedding."
  2021. arXiv:2104.09864.

Sparse attention, first wave

- R. Child et al. "Generating Long Sequences with Sparse Transformers." 2019.
  arXiv:1904.10509.
- J. Qiu et al. "Blockwise Self-Attention for Long Document Understanding."
  Findings of EMNLP 2020. arXiv:1911.02972.
- I. Beltagy, M. Peters, A. Cohan. "Longformer: The Long-Document Transformer."
  2020. arXiv:2004.05150.
- M. Zaheer et al. "Big Bird: Transformers for Longer Sequences." NeurIPS
  2020. arXiv:2007.14062.
- N. Kitaev, Ł. Kaiser, A. Levskaya. "Reformer: The Efficient Transformer."
  ICLR 2020. arXiv:2001.04451.
- A. Roy et al. "Efficient Content-Based Sparse Attention with Routing
  Transformers." TACL 2021. arXiv:2003.05997.
- J. Ainslie et al. "ETC: Encoding Long and Structured Inputs in Transformers."
  EMNLP 2020. arXiv:2004.08483.

Kernels and efficient attention

- T. Dao et al. "FlashAttention: Fast and Memory-Efficient Exact Attention with
  IO-Awareness." NeurIPS 2022. arXiv:2205.14135.
- T. Dao. "FlashAttention-2: Faster Attention with Better Parallelism and Work
  Partitioning." 2023. arXiv:2307.08691.
- PyTorch. "FlexAttention" documentation and tutorial, 2024–2026.
  https://pytorch.org/blog/flexattention/
- A. Katharopoulos et al. "Transformers are RNNs: Fast Autoregressive
  Transformers with Linear Attention." ICML 2020. arXiv:2006.16236.
- S. Wang et al. "Linformer: Self-Attention with Linear Complexity." 2020.
  arXiv:2006.04768.
- A. Gu, T. Dao. "Mamba: Linear-Time Sequence Modeling with Selective State
  Spaces." 2023. arXiv:2312.00752.

Long-context evaluation

- N. Liu et al. "Lost in the Middle: How Language Models Use Long Contexts."
  TACL 2024. arXiv:2307.03172.
- C.-P. Hsieh et al. "RULER: What's the Real Context Size of Your Long-Context
  Language Models?" 2024. arXiv:2404.06654.

Inference-time sparsity

- G. Xiao et al. "Efficient Streaming Language Models with Attention Sinks."
  ICLR 2024. arXiv:2309.17453. (StreamingLLM)
- Z. Zhang et al. "H2O: Heavy-Hitter Oracle for Efficient Generative Inference
  of Large Language Models." NeurIPS 2023. arXiv:2306.14048.
- Y. Li et al. "SnapKV: LLM Knows What You Are Looking For Before Generation."
  NeurIPS 2024. arXiv:2404.14469.
- C. Xiao et al. "InfLLM: Training-Free Long-Context Extrapolation for LLMs
  with an Efficient Context Memory." 2024. arXiv:2402.04617.
- J. Tang et al. "Quest: Query-Aware Sparsity for Efficient Long-Context LLM
  Inference." ICML 2024. arXiv:2406.10774.
- H. Jiang et al. "MInference 1.0: Accelerating Pre-filling for Long-Context
  LLMs via Dynamic Sparse Attention." NeurIPS 2024. arXiv:2407.02490.

Native and trainable sparsity

- J. Yuan et al. "Native Sparse Attention: Hardware-Aligned and Natively
  Trainable Sparse Attention." ACL 2025. arXiv:2502.11089. (NSA)
- E. Lu et al. "MoBA: Mixture of Block Attention for Long-Context LLMs." 2025.
  arXiv:2502.13189.
- DeepSeek-AI. "DeepSeek-V3.2-Exp" technical report and model card, 2025.
  https://github.com/deepseek-ai/DeepSeek-V3.2-Exp (DeepSeek Sparse Attention)

Evaluation and surveys

- P. Nawrot, R. Li, R. Huang, S. Ruder, K. Marchisio, E. M. Ponti. "The Sparse
  Frontier: Sparse Attention Trade-offs in Transformer LLMs." Findings of ACL
  2026, pp. 38667–38701. https://aclanthology.org/2026.findings-acl.1926.pdf
- Y. Sun et al. "Efficient Attention Mechanisms for Large Language Models: A
  Survey." 2025. arXiv:2507.19595.