# The models, one by one

Every model in the set earned its place by being the best in its size
class for a real job — not by being newest. All of them run comfortably
on a modern laptop CPU; a small GPU makes them fast.

## Qwen3 4B Instruct — the daily driver
~2.6 GB · Apache-2.0 · 32K context

The default. Strong chat, writing, summarization, and instruction
following at a size that loads in seconds. If you install one model,
install this one. Thinking/reasoning variants exist in the Qwen3 family;
the instruct build is pinned here because it answers directly, which is
what most people want from a 4B.

## Qwen3 1.7B — the sprinter
~1.4 GB · Apache-2.0 · 32K context

For jobs where speed beats depth: classification, tagging, routing,
draft replies, and running on genuinely old hardware. Also the right
choice as a "first stage" that decides whether a bigger model is even
needed.

## Llama 3.2 3B Instruct — the instruction follower
~2.0 GB · Llama 3.2 Community License · 128K context

Meta's small model punches above its weight on following multi-step
instructions exactly, and its long context makes it the pick for
"read this whole document and..." tasks on small machines. Note the
community license — fine for personal and most commercial use, read it
before shipping a product on it.

## Phi-4 Mini 3.8B — the reasoner
~2.5 GB · MIT · 128K context

Microsoft's Phi line is trained heavily on textbook-quality and
synthetic reasoning data. At this size it's the set's best at math,
logic, and structured problem solving. MIT licensed — the most
permissive license in the set.

## Gemma 3 4B — the one with eyes
~3.3 GB · Gemma Terms of Use · 128K context

The only multimodal model in the set: give it an image plus a question
and it answers about what it sees. Useful for describing screenshots,
reading charts, and accessibility tasks — all locally.

## Qwen2.5-Coder 3B Instruct — the coder
~1.9 GB · Apache-2.0 · 32K context

Purpose-trained for code: completion, explanation, docstrings, small
refactors, and "what does this error mean." Pair it with the chat model
for everything else.

## Nomic Embed Text v1.5 — the librarian (not a chat model)
~0.3 GB · Apache-2.0 · 8K context

Turns text into vectors so your machine can search your documents by
meaning. It's the foundation for local RAG: embed your notes, PDFs, or
codebase with this, keep the chat models for answering. It never
generates text — that's deliberate.

## Bundles

| Bundle | Models | ~Download | For |
|---|---|---|---|
| `starter` | Qwen3 4B | 2.6 GB | Trying it out |
| `everyday` | Qwen3 4B + Nomic Embed | 2.9 GB | Chat + document search |
| `coder` | Qwen3 4B + Coder 3B + Nomic Embed | 4.8 GB | Programming setup |
| `full_set` | All seven | ~14.0 GB | The whole shelf |

## Quantization, briefly

The pinned tags are 4-bit quantized (Q4_K_M where applicable): the
quality difference vs. full precision is small for models this size, and
the RAM savings are roughly 3–4×. That's what makes "runs on a normal
laptop" true instead of aspirational.
