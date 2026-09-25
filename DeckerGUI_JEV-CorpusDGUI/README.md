---
language:
- en
pretty_name: "INSTRUCT_JEV - TypeSafe AI Jev / System One Instruction Corpus"
license: mit
task_categories:
- text-generation
- question-answering
- text-classification
tags:
- instruct
- typesafe
- jev
- system-one
- choice
- noul
- score
- deckergui
configs:
- config_name: default
  data_files:
  - split: train
    path: train.jsonl
---

# INSTRUCT_JEV

**INSTRUCT_JEV** is an instruction corpus built from the **TypeSafe AI** documentation
for **Jev**, the first **System One** model. It is structured around the three TypeSafe
question primitives - **Choice**, **Noul** and **Score** - and mirrors the raw corpus
captured in `deckerGUI-jev_corpus_RAW`.

## Credits

INSTRUCT_JEV is a **DeckerGUI** project and exists because of the work below.

| Who | Contribution | Link |
|-----|--------------|------|
| **TypeSafe AI** | Jev - the first System One model - and the Choice / Noul / Score primitives. Author of the documentation this corpus is built from. | <https://typesafe.ai> - <https://docs.typesafe.ai> |
| **DeckerGUI** | Compiled the corpus into instruction rows, published the dataset and tooling. | <https://deckergui.my> |
| **KrackedDevs** | Community credit and support. | KrackedDevs |
| **CTECX** | Knowledge / corpus partner. | CTECX |

All documentation, concepts, API design and examples are the work of **TypeSafe AI**
(<https://typesafe.ai>). Jev, System One and the Choice / Noul / Score primitives are
TypeSafe's. This corpus is compiled and redistributed under their MIT-licensed public
documentation at <https://docs.typesafe.ai>.

> Corpus and concepts are the property of TypeSafe AI. Jev, System One, and the Choice / Noul / Score primitives are TypeSafe's. Used and redistributed under their MIT-licensed public documentation. Compiled by DeckerGUI.
> Source: TypeSafe AI documentation (Jev / System One) - https://docs.typesafe.ai
> Compiled by **DeckerGUI**.

## Repository

Source, builder and raw mirror: <https://github.com/ctaxnagomi/instruct-jev>
HuggingFace dataset: <https://huggingface.co/datasets/ctaxnagomi/INSTRUCT_JEV>

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](https://github.com/ctaxnagomi/instruct-jev/blob/main/CONTRIBUTING.md)
and [CONTRIBUTORS.md](https://github.com/ctaxnagomi/instruct-jev/blob/main/CONTRIBUTORS.md) - contributors are added to
the credits table in the same pull request.

## Scope

The **RAW** mirror captures the full cleaned TypeSafe AI documentation corpus
(`deckerGUI-jev_corpus_RAW`, 128 files). The published instruction
rows are curated from it: every extracted typed Choice / Noul / Score example is kept,
plus the conceptual documentation (`_primitives`, `_typesafe_foundations`, `_patterns`,
`_demos` and the root pages). The large per-heading SDK / cookbook chunk set is kept in
the RAW mirror but is not expanded into instruction rows.

## Function types

Every row is tagged with one of the three TypeSafe System One function types:

| `function_type` | Primitive | Answer shape |
|-----------------|-----------|--------------|
| `choice` | Choice - pick one option from a list | `choice`, `probabilities`, `confidence` |
| `noul` | Noul - is the statement true? | `noul` (0-1) |
| `score` | Score - rate along ordered levels | `score`, `legend`, `probabilities`, `confidence` |

## Stats

- Rows: **122**
- choice: **49** / noul: **51** / score: **22**
- Rows with an extracted typed question block: **24** (of which **7** include typed answers)
- Unique source documents: **114** (from 128 captured files)

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Sequential row id |
| `dataset` | string | `INSTRUCT_JEV` |
| `instruction` | string | The task / question |
| `input` | string | Context or state |
| `output` | string | The expected answer |
| `state` | json | TypeSafe state when available |
| `question_block` | json | Typed Choice / Noul / Score question objects |
| `answer_block` | json | Typed answers |
| `question_count` | int | Number of questions in the block |
| `has_answer` | bool | Whether a typed answer block was extracted |
| `model` | string | Model alias shown in docs (`jev-latest`) |
| `function_type` | string | `choice` \| `noul` \| `score` |
| `doc_title` | string | Source document title |
| `section` | string | Source section heading |
| `category` | string | Corpus category |
| `source` | string | Raw corpus relative path |
| `tags` | array | Search tags |
| `credit` | string | Attribution |

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("ctaxnagomi/INSTRUCT_JEV")
print(dataset["train"][0])
```

Per-primitive subsets are published alongside the full set: `choice.jsonl`,
`noul.jsonl`, `score.jsonl`.

## License

MIT (c) DeckerGUI - see [LICENSE](https://github.com/ctaxnagomi/instruct-jev/blob/main/LICENSE). Upstream TypeSafe AI
documentation is MIT-licensed; see their original terms at <https://docs.typesafe.ai>.
Compiled by DeckerGUI (https://deckergui.my).
