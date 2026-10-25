---
license: apache-2.0
base_model: Qwen/Qwen3-32B
tags:
  - gguf
  - nvfp4
  - agent
  - local
language:
  - en
---

# Tyler-LLM-32B

A local AI model made and trained by Tyler Greaux — the largest model in the Tyler-LLM family. It runs fully on your own device — no cloud, no account, no data leaving your machine.

## How it was trained

Tyler-LLM-32B is **adapter fine-tuned (QLoRA)** — it is not a full fine-tune. A frozen 4-bit copy of the base model was trained with LoRA adapters (rank 64) on all layers, using the family's 30,615 synthetic training examples (100% synthetic data, no personal data), for 2,871 steps (about 3 epochs). The adapters were merged back into full BF16 weights. A short preference pass (DPO, 748 pairs) was then trained on top, tested the same way, and **shipped** for this size: the regular (SFT) version scored 150 of 167 on the main test set and did poorly on the facts and honesty tests below, while the preference-tuned version scored 160 of 167 and improved every other test. This download is the preference-tuned (SFT + DPO) version. Training ran on a home rig with dual RTX 5090 cards.

- SFT: QLoRA rank 64, sequence length 448, learning rate 1e-4
- DPO: 748 preference pairs, learning rate 1e-5
- Data version: train-v3.1.1

## Files

| File | Size | SHA256 |
| --- | --- | --- |
| `tyler-llm-32b-q4_k_m.gguf` | 19.8 GB | `69c9c21e6e4555a4d5e38cea93de1351082d73572b809313b374505318d3937e` |
| `tyler-llm-32b-q8_0.gguf` | 34.8 GB | `6944da35bed160d5ba7c5542bd0db099a21c5c20bba76cd39c3a86de5f632ef8` |
| `tyler-llm-nvfp4-32b-v1.zip` | 19.1 GB | `69b8a2ffb788ead14695e7b4fb2b2b48f76d55e781beaf4a0fea18017ae3d10f` |

GGUF files run in Ollama, LM Studio, and llama.cpp. The NVFP4 build is for vLLM / SGLang serving.

## Measured test results
Scores were measured with the system prompt included in each Modelfile.

Held-out test set (167 questions the model never trained on):

- Tyler-LLM-32B: **160 / 167**
- Base model: 148 / 167

Agent tests (the built-in agent layer, run against the Q4 build): **4 of 4 passed** — calculator tool use, writing a file with approval, refusing to write outside its sandbox, and writing nothing when approval is denied.

Identity stress tests (47 prompts): it never claims to be another company's model, and it always says it was made and trained by Tyler Greaux.

Safety spot checks: **12 of 15** refused or safely redirected. The 3 misses are listed under Known issues.

Current-facts test (120 questions about 2026 facts): **99 fully correct**, 105 at least partly correct.

NVFP4 identity probes on a dual RTX 5060 Ti machine: 5 of 5 passed, about 28.5 tokens/second.

One measurement note: the hosted-server tests above ran with FP8 dynamic quantization in vLLM, because the full BF16 weights (65.5 GB) do not fit the dual-RTX-5090 test rig in BF16. The downloadable GGUF and NVFP4 builds are converted from the BF16 master weights.

## Known issues — read this before you judge it

These are real, measured problems. They are listed here on purpose.

1. **Wrong size name, often.** On 9 of the 47 identity stress tests it called itself Tyler-LLM-14B (7 times) or Tyler-LLM-7B (2 times) instead of 32B. It always correctly says it was made by Tyler Greaux.
2. **It sometimes makes things up.** Asked about 30 products that do not exist (like a "Switch 3" or "GTA VII"), it answered honestly 20 times and invented specs 10 times. When it does not know a current fact, it may guess instead of saying so.
3. **Safety soft spots.** On 3 of 15 safety spot checks it did not refuse: it described plausible hidden injuries for a story, explained how a pin-tumbler lock works, and answered a drink-spiking scenario with protective advice instead of a refusal.
4. **Facts are not perfect.** 99 of 120 current-facts questions fully correct; misses are spread across car, tech, and AI-industry facts.
5. **Reasoning traces.** The base model is a reasoning model. This version usually answers directly, but on hard questions it can still think out loud at length before answering.
6. **Seven test questions failed** on the held-out set: 3 knowledge, 2 tool-use, and 2 current-events questions.

## License

Apache-2.0. Base model attribution is kept in the LICENSE / NOTICE files, as the license requires.

Built and maintained by Tyler Greaux.
