# gendocs

A collection of technical notes: measured write-ups, source-verified
explanations, and reference tables. Most documents state the versions and
sources they were checked against; claims that are inferred rather than
observed are marked in the text.
I (cognominal) asked deepseek to write them for
my own instruction.

## Documents

| Document | Theme | Summary |
|---|---|---|
| [`bindings.md`](bindings.md) | Desktop | Compares window and workspace bindings in Omarchy 4.5, LazyVim, and tuios. Also explains the Omarchy → Ghostty → tuios → LazyVim key-routing stack, includes Ghostty's effective bindings, and calls out the collisions between layers. |
| [`minimize.md`](minimize.md) | Desktop | How Omarchy 4.5 emulates window minimization: the window is parked on `special:minimized`, the dock restores it, and there is no stock restore key. Covers the local keyboard restore, scripting, and caveats. |
| [`bootloaders.md`](bootloaders.md) | Systems | A history of Linux bootloaders, x86-centric but covering non-x86 and embedded loaders: LILO, GRUB, SYSLINUX, EFI/UEFI, and where boot has ended up. Includes a timeline and boot-chain comparison. |
| [`curly-hash.md`](curly-hash.md) | Raku | Why `{ ... }` in Raku can be a block, a hash constructor, or a hash subscript. Explains the compile-time hash heuristic, when it does not run, and gives a verified decision table. |
| [`natives.md`](natives.md) | Raku | Native and C-like arrays in Raku: shaped native arrays, unboundedown arrays, indexing and slicing, out-of-bounds behavior, aliasing, and C interoperability. Ends with a gotcha checklist and cheat sheet. |
| [`scalar.md`](scalar.md) | Raku | Boxing and integer representation in Raku: when values become objects, what `Scalar` containers are, and why small integers from `-1..14` are interned. |
| [`jq-tut.md`](jq-tut.md) | Data | A jq tutorial in two parts: the filter model and core operations, then a Nushell-based running example that reshapes `tuios ls --json` and `tuios worktree ls --json`. Includes a cheat sheet and field map. |
| [`sparse-attention.md`](sparse-attention.md) | LLMs | A long-form guide to sparse attention for long-context transformers: prerequisite background, the cost model, pattern taxonomy, kernels, measurements, failure modes, and design choices. No original benchmarks were run. |
| [`tokenization.md`](tokenization.md) | LLMs | Measured notes on tokenization and Unicode: why non-Latin alphabetic scripts cost more tokens, which problems are cost versus correctness bugs, how to measure a tokenizer, and what can actually be fixed. |
| [`karpathy.md`](karpathy.md) | Archive | Karpathy's 100 most-liked original posts, ranked by likes, with counts pulled 2026-11-15 and full text for long-form posts. |
