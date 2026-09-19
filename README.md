# instruct-jev

**INSTRUCT_JEV** — a TypeSafe AI **Jev / System One** instruction corpus, compiled by
**DeckerGUI** from the public TypeSafe AI documentation.

[![HuggingFace](https://img.shields.io/badge/🤗%20dataset-ctaxnagomi%2FINSTRUCT__JEV-yellow)](https://huggingface.co/datasets/ctaxnagomi/INSTRUCT_JEV)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

> **Jev** is the first **System One** model. Its API is built on three question
> primitives — **Choice** (pick one option), **Noul** (is it true?) and
> **Score** (rate along ordered levels). This repository captures that documentation and
> compiles it into instruction rows.

- 119 instruction rows · choice 47 / noul 51 / score 21
- 128 source files captured · 114 unique documents
- Published as a HuggingFace dataset: <https://huggingface.co/datasets/ctaxnagomi/INSTRUCT_JEV>

## Repository layout

```
instruct-jev/
├── build_instruct_jev.py        # builder: reads the raw docs, writes the dataset
├── deckerGUI-jev_corpus_RAW/    # cleaned mirror of the source corpus + manifest.json
└── DeckerGUI_JEV-CorpusDGUI/    # build output (the published dataset)
    ├── train.jsonl              # all rows
    ├── choice.jsonl             # per-primitive subsets
    ├── noul.jsonl
    ├── score.jsonl
    ├── metadata.json            # stats, schema, attribution
    ├── stats.json
    └── README.md                # the HuggingFace dataset card (generated)
```

Source documents are the `.md` / `.txt` / `.json` files at the repository root and in the
`_primitives`, `_typesafe_foundations`, `_patterns`, `_demos` and `_client_sdks` capture
folders. Non-text browser artifacts (`_pdf/`, `_webpage/`, `_avif-file/`, `_webp/`) are not
corpus sources and are excluded from version control.

## Build

Requires Python 3.10+ (standard library only).

```bash
python DeckerGUI_JEV-CorpusDGUI/build_instruct_jev.py
```

The script is idempotent: it re-mirrors the cleaned corpus into
`deckerGUI-jev_corpus_RAW/` and rewrites every file in `DeckerGUI_JEV-CorpusDGUI/`.

## Use

```python
from datasets import load_dataset

ds = load_dataset("ctaxnagomi/INSTRUCT_JEV")
print(ds["train"][0])
```

## Credits

INSTRUCT_JEV is a **DeckerGUI** project.

| Who | Contribution | Link |
|-----|--------------|------|
| **TypeSafe AI** | Jev — the first System One model — and the Choice / Noul / Score primitives. Author of the documentation this corpus is built from. | <https://typesafe.ai> · <https://docs.typesafe.ai> |
| **DeckerGUI** | Compiled the corpus into instruction rows; published the dataset and tooling. | <https://deckergui.my> |
| **KrackedDevs** | Community credit and support. | KrackedDevs |
| **CTECX** | Knowledge / corpus partner. | CTECX |

> Corpus and concepts are the property of **TypeSafe AI**. *Jev*, *System One*, and the
> *Choice / Noul / Score* primitives are TypeSafe AI's and are used and redistributed under
> their MIT-licensed public documentation (<https://docs.typesafe.ai>). Compiled by
> **DeckerGUI**.

## Contributing

Contributions are welcome — a fixed typo, a new extracted example, a better builder.
See [CONTRIBUTING.md](CONTRIBUTING.md). Contributors are listed in
[CONTRIBUTORS.md](CONTRIBUTORS.md) and added to the credits table in the same pull request.

## Citation

```bibtex
@misc{instruct_jev,
  title  = {INSTRUCT_JEV: TypeSafe AI Jev / System One Instruction Corpus},
  author = {DeckerGUI},
  year   = {2026},
  url    = {https://github.com/ctaxnagomi/instruct-jev}
}
```

## License

[MIT](LICENSE) © 2026 DeckerGUI. Upstream documentation is MIT-licensed by
[TypeSafe AI](https://typesafe.ai).
