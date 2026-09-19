# Contributing to INSTRUCT_JEV

Thanks for helping improve INSTRUCT_JEV — a TypeSafe AI **Jev / System One** instruction
corpus compiled by **DeckerGUI**.

## Ways to contribute

- **Fix or improve a row** — a clearer `instruction`, a corrected `output`, a better tag.
- **Add an extracted example** — a typed Choice / Noul / Score example that the builder missed.
- **Improve the builder** — `DeckerGUI_JEV-CorpusDGUI/build_instruct_jev.py` (sectioning,
  extraction, dedup, schema).
- **Docs** — the README, schema tables and attribution text.

## Getting set up

Requires Python 3.10+ (standard library only; there is nothing to install).

```bash
git clone https://github.com/ctaxnagomi/instruct-jev
cd instruct-jev
python DeckerGUI_JEV-CorpusDGUI/build_instruct_jev.py
```

The build is idempotent. It re-mirrors the cleaned corpus into
`deckerGUI-jev_corpus_RAW/` and rewrites every file in `DeckerGUI_JEV-CorpusDGUI/`
(`train.jsonl`, the per-primitive `choice.jsonl` / `noul.jsonl` / `score.jsonl`,
`metadata.json`, `stats.json`, `README.md`).

## Rules

1. **Never hand-edit generated files.** Change the builder or the source docs, then re-run
   the build. Generated files are: everything in `DeckerGUI_JEV-CorpusDGUI/` and
   `deckerGUI-jev_corpus_RAW/`.
2. **Attribute upstream.** TypeSafe AI material stays credited. Do not remove or weaken the
   TypeSafe AI attribution in `README.md`, `metadata.json` or `LICENSE`.
3. **Keep the schema stable.** Adding a field is fine (document it in the README schema
   table); renaming or removing one needs a version bump in the builder (`VERSION`).
4. **One thing per pull request.** Small, focused PRs are reviewed faster.

## How to become a contributor

1. Fork the repository and create a branch: `git checkout -b my-change`.
2. Make your change and re-run the builder so generated files are consistent.
3. Add yourself to [CONTRIBUTORS.md](CONTRIBUTORS.md) — add a row to the **Contributors**
   table with your name/handle and what you did. (Maintainer and organisation credits are
   already listed; add yourself under **Contributors**.)
4. Commit, push, and open a pull request describing the change and how you verified it.

Your name will appear in `CONTRIBUTORS.md` once the PR is merged.

## Pull request checklist

- [ ] Builder runs clean: `python DeckerGUI_JEV-CorpusDGUI/build_instruct_jev.py`
- [ ] Generated files are regenerated, not hand-edited
- [ ] TypeSafe AI attribution intact
- [ ] `CONTRIBUTORS.md` updated (if you are a new contributor)
- [ ] PR description says what changed and why

## Credits

See [CONTRIBUTORS.md](CONTRIBUTORS.md) for the full list: **DeckerGUI** (project),
**TypeSafe AI** (Jev / System One), **KrackedDevs**, **CTECX**.

## License

By contributing you agree your contribution is licensed under the repository's
[MIT License](LICENSE).
