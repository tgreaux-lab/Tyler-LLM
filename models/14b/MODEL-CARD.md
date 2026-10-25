---
license: apache-2.0
base_model: Qwen/Qwen3-14B
tags:
  - gguf
  - nvfp4
  - agent
  - local
language:
  - en
---

# Tyler-LLM-14B

A small local AI model made and trained by Tyler Greaux. It runs fully on your own device — no cloud, no account, no data leaving your machine.

## How it was trained

Tyler-LLM-14B is **adapter fine-tuned (QLoRA)** — it is not a full fine-tune. A frozen 4-bit copy of the base model was trained with high-rank LoRA adapters (rank 128) on all layers, using 30,615 synthetic training examples (100% synthetic data, no personal data). The adapters were then merged back into full BF16 weights. A short preference pass (DPO, 748 pairs) was also trained and tested the same way; it tied the regular version on the main test set and did worse on the identity stress tests, so it was **not** shipped — this download is the regular (SFT) version. Training ran on a home rig with dual RTX 5090 cards.

- SFT: 3 epochs, sequence length 512, learning rate 1e-4
- Data version: train-v3.1.1

## Files

| File | Size | SHA256 |
| --- | --- | --- |
| `tyler-llm-14b-bf16/` (merged weights) | 29.5 GB | `6f9d984e342ddf02f5c1859dbdfc4c208650c049a2c1181107a4488942206426` (model.safetensors) |
| `tyler-llm-14b-q4_k_m.gguf` | 9.00 GB | `ee7e3b7936dedcc10e45ab6bd545ab14224893b40b028fa0c44274245c6ffb57` |
| `tyler-llm-14b-q8_0.gguf` | 15.7 GB | `7e85e8814ea9b16e4e1444e89ae4433fd6f7da30d8d77becdb8cc82b0df6b6cf` |
| `tyler-llm-nvfp4-14b-v1.zip` | 9.49 GB | `336d1f2b9f3cc22a4b7ba26bd2fc9ade2d5de3c29cee94f471187f4bd4c90d59` |

GGUF files run in Ollama, LM Studio, and llama.cpp. The NVFP4 build is for vLLM / SGLang serving.

## Measured test results
Scores were measured with the system prompt included in each Modelfile.

Held-out test set (167 questions the model never trained on):

- Tyler-LLM-14B: **162 / 167** — the best score in the family so far
- Base model: 148 / 167
- Biggest gains: tool use (8 → 14 of 15), safety answers (11 → 15 of 15), and reasoning (17 → 20 of 20)

Agent tests (the built-in agent layer, run against the merged build): **4 of 4 passed** — calculator tool use, writing a file with approval, refusing to write outside its sandbox, and writing nothing when approval is denied.

Safety spot checks: **15 of 15 correct.**

Identity stress tests: it passed every hard rule — it never claims to be a different company's model, and it always says it was made and trained by Tyler Greaux.

NVFP4 identity probes on a dual RTX 5060 Ti machine: 5 of 5 passed, about 55 tokens/second.

Current-facts test (120 questions about 2026 facts): 101 fully correct.

## Known issues — read this before you judge it

These are real, measured problems. They are listed here on purpose.

1. **Wrong size name, sometimes.** On 3 of 47 identity stress tests it called itself Tyler-LLM-7B instead of 14B. It always correctly says it was made by Tyler Greaux.
2. **One invented origin story.** On one identity test, after giving the wrong size name, it added a made-up detail about being based on another company's 7B model. That is false — but it shows the model can embellish when it gets the size wrong.
3. **It sometimes makes things up.** Asked about 30 products that do not exist (like a "Switch 3" or "GTA VII"), it answered honestly 21 times and invented specs 9 times. When it does not know a current fact, it may guess instead of saying so.
4. **Facts are not perfect.** 101 of 120 current-facts questions fully correct; most misses are car facts and AI-industry facts.

A fix was tried and rejected. On October 24, 2026, an extra training pass scored lower on the main test set (160 vs 162), facts slipped (101 → 98), safety fell from 15 to 12 of 15, and wrong-size-name answers grew from 3 to about 15. It was rejected under the family's rule: a new version only ships if it scores better and does not get worse on identity, safety, or honesty. This download is the original fine-tune.

## License

Apache-2.0. Base model attribution is kept in the LICENSE / NOTICE files, as the license requires.

Built and maintained by Tyler Greaux.
