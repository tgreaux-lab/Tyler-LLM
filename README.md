# Tyler-LLM

A family of small AI models made and trained by Tyler Greaux. They run fully
on your own hardware — no cloud, no account, no data leaving your machine.

Five sizes, one design: honest about what they know, careful with tools, and
clear about who made them. Every size was tested against its own base model
on a held-out test set of 167 questions it never trained on, and every size
beat its base. Each model's card lists its measured results **and** its known
problems, by name. Read the cards before you judge the models.

## The family

| Model | Parameters | How it was trained | Held-out test | Its base model | Downloads (GGUF Q4_K_M / Q8_0 / NVFP4) |
|---|---|---|---|---|---|
| [Tyler-LLM-1.7B](https://huggingface.co/tgreaux/Tyler-LLM-1.7B) | 1.72 B | Full fine-tune | **155 / 167** | 138 / 167 | 1.11 GB / 1.83 GB / 1.24 GB |
| [Tyler-LLM-3B](https://huggingface.co/tgreaux/Tyler-LLM-3B) | 4.02 B | Full fine-tune | **157 / 167** | 141 / 167 | 2.50 GB / 4.28 GB / 2.55 GB |
| [Tyler-LLM-7B](https://huggingface.co/tgreaux/Tyler-LLM-7B) | 7.62 B | Adapter tune (QLoRA) + preference pass | **159 / 167** | 153 / 167 | 4.68 GB / 8.10 GB / 5.19 GB |
| [Tyler-LLM-14B](https://huggingface.co/tgreaux/Tyler-LLM-14B) | 14.77 B | Adapter tune (QLoRA) | **162 / 167** | 148 / 167 | 9.00 GB / 15.7 GB / 9.49 GB |
| [Tyler-LLM-32B](https://huggingface.co/tgreaux/Tyler-LLM-32B) | 32.76 B | Adapter tune (QLoRA) + preference pass | **160 / 167** | 148 / 167 | 19.8 GB / 34.8 GB / 19.1 GB |

About the "3B" name: it is the family label. That model actually has
4,022,468,096 parameters (about 4.0 billion), inherited from its base model.
That is stated here on purpose — the label is the family name, not an exact
count.

- **1.7B / 3B** — the small end. Phone-class and small-device tier; fast,
  limited, and (at 1.7B) shipped with openly listed failures.
- **7B** — the daily driver for a normal computer.
- **14B** — the best balance in the family, and its best test score.
- **32B** — the flagship, for a serious local machine or a small server.

Per-size model cards live in [`models/`](models/) and on each model's
Hugging Face page.

## Quick start

**Ollama** — one line, no download step:

```bash
ollama run hf.co/tgreaux/Tyler-LLM-14B:Q4_K_M
```

Swap in any size (`Tyler-LLM-1.7B`, `-3B`, `-7B`, `-14B`, `-32B`) and either
quant (`Q4_K_M` or `Q8_0`). Each folder under [`models/`](models/) also has a
`Modelfile` for use with a locally downloaded GGUF file.

**LM Studio / llama.cpp** — download a GGUF file from the model's
Hugging Face page and load it.

**Servers (vLLM / SGLang)** — use the NVFP4 zip from the model's
Hugging Face page.

## Verify your download

Every published file has a SHA-256 checksum. The full list is in
[`SHA256SUMS.txt`](SHA256SUMS.txt), on each model card, and in the per-size
manifest files under [`models/`](models/).

```bash
# Linux / macOS
sha256sum tyler-llm-14b-q4_k_m.gguf

# Windows
certutil -hashfile tyler-llm-14b-q4_k_m.gguf SHA256
```

Compare the output with the value in `SHA256SUMS.txt`. If they do not match,
do not use the file.

## The agent runtime

[`agent/`](agent/) holds a small agent harness that ships with the family.
It is standard-library-only Python with a strict safety design:

- It talks to the model only on your own machine (loopback). It refuses any
  non-loopback address, in code.
- The model may only call an allow-list of tools: a calculator, the clock,
  unit conversion, and file read/write jailed to a sandbox folder.
- Every file write needs a human "yes" at the terminal, every time.
- No shell tool. No network tools. No exceptions.
- Its memory is a plain local file you can read, edit, or delete.

```bash
python agent/agent.py
```

## The data

The models were trained on 100% synthetic data — no personal data, no real
person's data, nothing scraped from anyone. See [`DATASET.md`](DATASET.md)
for what the data is, how it was checked, and what was kept out.

## Honest limits

- Knowledge is current through **October 2026**. The models are not live and
  do not browse.
- Small models sometimes invent an answer instead of saying "I don't know."
  The smaller sizes do this more. Each card says how often, measured.
- The 1.7B has known identity and safety failures. They are listed on its
  card, by test name. It is published for completeness, with the failures
  stated, not hidden.
- Extra training passes that made any of these problems worse were rejected,
  even when they raised the main test score. The family rule: a new version
  only ships if it scores better **and** does not get worse on identity,
  safety, or honesty.

## License

Apache-2.0. See [`NOTICE`](NOTICE) for the base-model attributions the
license requires.

Built and maintained by Tyler Greaux.
