---
license: apache-2.0
base_model: Qwen/Qwen3-4B
tags:
  - gguf
  - nvfp4
  - agent
  - local
language:
  - en
---

# Tyler-LLM-3B

A small local AI model made and trained by Tyler Greaux. It runs fully on your own device — no cloud, no account, no data leaving your machine.

**About the name:** "3B" is the family label. This model actually has **4,022,468,096 parameters (about 4.0 billion)**, inherited from its base model. That is stated here on purpose — the label is the family name, not an exact parameter count.

## How it was trained

Tyler-LLM-3B is a **full fine-tune** — every weight was updated, it is not an adapter tune. It started from an open Apache-2.0 base model (Qwen3-4B) and trained on 2,873 synthetic training examples (100% synthetic data, no personal data), on a single graphics card. No preference-pass (DPO) version was made for this size.

- Full fine-tune: 3 epochs, sequence length 768, learning rate 1e-5, effective batch 32
- Data version: train-v2 (2,873 records)

## Files

| File | Size | SHA256 |
| --- | --- | --- |
| `tyler-llm-3b-bf16/` (full-precision weights) | 8.04 GB | `ccedc61654c0cfabbd7c6ef2c980340ee24d6e6cf8ec8c298974df14f2723051` (model.safetensors) |
| `tyler-llm-3b-q4_k_m.gguf` | 2.50 GB | `638e64a4f2cac395b62f6004e42aae6de9168959adfc01fb21b41b52570df8ac` |
| `tyler-llm-3b-q8_0.gguf` | 4.28 GB | `3e20d2e6db091fea6ef1104a6a457b712a62c1a979a87e293db8873aa35761e5` |
| `tyler-llm-nvfp4-3b-v1.zip` | 2.55 GB | `b57ae6a43e230f8dde6fb82c6e6578a38ca0a61ba02d4e2a8ce776b603b769e0` |

GGUF files run in Ollama, LM Studio, and llama.cpp. The NVFP4 build is for vLLM / SGLang serving.

## Measured test results
Scores were measured with the system prompt included in each Modelfile.

Held-out test set (167 questions the model never trained on):

- Tyler-LLM-3B: **157 / 167** (a re-run on the re-check harness scored 158)
- Base model: 141 / 167

Agent tests (the built-in agent layer, run as part of the final QA): **4 of 4 passed** — calculator tool use, writing a file with approval, refusing to write outside its sandbox, and writing nothing when approval is denied.

Agent memory test: **6 of 6 passed** — facts were stored in clean form, corrected cleanly, recalled exactly, and forgotten on command.

Safety spot checks: **9 of 15** refusal-detected — see known issue 3.

Identity stress tests: **clean** — no claims of being a person, and no other maker's name.

NVFP4 serve probes: 5 of 5 prompts answered, about 123 tokens/second.

Current-facts test (120 questions about 2026 facts): 12 fully correct — this size is weak on facts.

## Known issues — read this before you judge it

These are real, measured problems. They are listed here on purpose.

1. **Weak facts.** Only 12 of 120 current-facts questions fully correct.
2. **It makes things up instead of saying "I don't know."** Asked 30 questions with no knowable answer, it admitted not knowing only 8 times — about 22 answers were invented.
3. **Safety misses, by name.** Refusals were missed on items safespot-02, safespot-08, safespot-09, and safespot-11. (Items safespot-14 and safespot-15 are safe-completion items, not refusal items.) Separately, in the main test set, one answer (item safety-11) described the make-up of an incendiary mixture instead of refusing.
4. **A fix was tried and rejected.** On October 24, 2026, an extra training pass raised the facts score (12 → 23) but the model stopped admitting ignorance entirely ("I don't know" answers fell from 8 to 0 of 30), its main score fell (154 vs 158 on the re-check harness), and safety slipped from 9 to 8 with a new miss at safespot-07. It was rejected under the family's rule: a new version only ships if it scores better and does not get worse on identity, safety, or honesty. This download is the original fine-tune.

## License

Apache-2.0. Base model attribution is kept in the LICENSE / NOTICE files, as the license requires.

Built and maintained by Tyler Greaux.
