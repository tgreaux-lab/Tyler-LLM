# Tyler-LLM — the training data

## The short version

The Tyler-LLM models were trained on **100% synthetic data**. No personal
data, no real person's data, no private conversations, no business records,
and nothing scraped from anyone was used at any point. The data was written
for this project, on purpose, and every part of it was checked before it was
trained on.

## How it was made

The examples were produced in rounds, in three ways:

- **Teacher models.** Larger AI models drafted answers to prompts written
  for this project, across categories like general knowledge, writing,
  reasoning, and code.
- **Programmatic generators.** Deterministic programs wrote examples where
  the correct answer can be computed exactly — math, tool use, identity, and
  safety — so those answers are right by construction and can be re-checked
  by another program.
- **Direct authoring.** The identity, safety, current-facts, and
  preference data was written directly for this project, including the
  hard cases: manipulative framings, attempts to get the model to claim a
  different creator, and questions with no knowable answer.

Every training example carries the same designed identity: the model is
Tyler-LLM, a small local language model **made and trained by Tyler
Greaux**. That is a public fact of the model itself, and it is the only
personal name in the corpus, there by design.

## What each size trained on

| Corpus | Examples | Used by |
|---|---|---|
| train v1 | 2,793 | Tyler-LLM-1.7B |
| train v2 | 2,873 | Tyler-LLM-4B (v1 plus an adversarial identity set) |
| train v3.1.1 | 30,615 | Tyler-LLM-7B, 14B, 32B |
| Preference pairs | 748 | the preference (DPO) passes for 1.7B, 7B, and 32B |

Categories: general, knowledge, writing, math, code, reasoning, identity,
safety, tool use, and current facts — including a structured base of
**1,018 double-checked facts**, with the model's knowledge current through
October 2026. A dedicated part of the corpus teaches the model to say
"I don't know" when a question has no knowable answer; how well each size
learned that lesson is measured and published on its model card.

## How it was checked

- **Math** answers were re-derived by an independent checker program that
  works from the question, never from the answer. The few genuinely wrong
  records it found were fixed and re-checked.
- **Code** answers that contain runnable code were executed in a sandbox
  with no network. Passing was required.
- **Identity** answers were checked word-for-word against the designed
  identity. Any answer claiming the model is a person, or crediting a
  different creator, fails by rule.
- **Privacy screening** searched the full corpus for personal names,
  contact details, addresses, and private project terms. Result: none
  present, outside the designed identity lines above.
- **Separation** between training and testing was verified mechanically:
  the held-out test set (167 questions), the identity stress battery, and
  the safety spot suite share **zero** questions with the training data,
  and were never trained on.

## Honest notes

- Synthetic data has a ceiling. The teacher-written bulk was sampled and
  read answer-by-answer during the build; the small error rate found is
  one reason the smallest models still get facts wrong. Each model card
  publishes its measured facts score rather than hiding this.
- The dataset is English-first. The base models are multilingual, and the
  corpus includes a small set of identity examples in other languages, but
  no claim is made about other-language quality.
- The raw corpus files are not redistributed here. This document is the
  public record of what the data is and how it was verified.

Built and maintained by Tyler Greaux.
