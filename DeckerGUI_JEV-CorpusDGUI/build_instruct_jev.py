#!/usr/bin/env python3
"""INSTRUCT_JEV corpus builder (DeckerGUI).

Reads the raw TypeSafe AI (JEV / System One) documentation corpus, mirrors a
cleaned copy into deckerGUI-jev_corpus_RAW/, and compiles the INSTRUCT_JEV
instruction dataset following the RAW corpus taxonomy and the three TypeSafe
System One question primitives: choice, noul, score.

Attribution: documentation (c) TypeSafe AI - https://typesafe.ai - MIT license.
Compiled / curated by DeckerGUI (https://deckergui.my).

Outputs
-------
deckerGUI-jev_corpus_RAW/
    mirror of cleaned source docs (taxonomy preserved) + manifest.json
DeckerGUI_JEV-CorpusDGUI/
    train.jsonl, choice.jsonl, noul.jsonl, score.jsonl,
    metadata.json, README.md, stats.json
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "deckerGUI-jev_corpus_RAW"
BUILD_DIR = ROOT / "DeckerGUI_JEV-CorpusDGUI"

DATASET_NAME = "INSTRUCT_JEV"
REPO = "ctaxnagomi/INSTRUCT_JEV"
VERSION = "1.0.0"
LICENSE = "MIT"
GITHUB_REPO = "https://github.com/ctaxnagomi/instruct-jev"
PROJECT = "DeckerGUI"
PROJECT_URL = "https://deckergui.my"
SOURCE_URL = "https://docs.typesafe.ai"
SOURCE_NAME = "TypeSafe AI documentation (Jev / System One)"
CREDIT = "TypeSafe AI - https://typesafe.ai"
CREDIT_NOTE = (
    "Corpus and concepts are the property of TypeSafe AI. Jev, System One, and "
    "the Choice / Noul / Score primitives are TypeSafe's. Used and redistributed "
    "under their MIT-licensed public documentation. Compiled by DeckerGUI."
)

TEXT_EXT = {".md", ".txt", ".json"}
SKIP_DIRS = {RAW_DIR.name, BUILD_DIR.name, "node_modules", ".git", "__pycache__"}
# Repository meta files that live at the repo root and are NOT part of the source corpus.
SKIP_FILES = {
    "README.md", "LICENSE", "CONTRIBUTING.md", "CONTRIBUTORS.md",
    "CODE_OF_CONDUCT.md", "SECURITY.md", "CHANGELOG.md", "NOTICE.md",
}

FUNCTION_TYPES = ("choice", "noul", "score")

SKIP_GENERIC_CATEGORIES = {"_client_sdks"}

DOC_INDEX_RE = re.compile(r"^> ## Documentation Index\n(?:>.*\n)+\s*", re.M)
HEAD_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
JSON_FENCE_RE = re.compile(r"```json[^\n]*\n(.*?)```", re.S)
JSX_RE = re.compile(r"<TypesafeExample\b(.*?)/>", re.S)
BACKTICK = re.compile(r"`([^`]+)`")

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "are", "you", "your",
    "can", "use", "using", "when", "question", "questions", "type", "types",
    "will", "not", "but", "its", "into", "over", "each", "they", "them",
    "their", "have", "has", "does", "how", "what", "which", "one", "two",
    "api", "doc", "docs", "page", "pages", "http", "https", "theme", "null",
    "true", "false", "string", "object", "array", "value", "values", "field",
}


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def strip_example_component(text: str) -> str:
    """Remove the repeated `export function TypesafeExample(...) {...}` helper."""
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("export function TypesafeExample"):
            saw_return = False
            j = i
            while j < len(lines):
                if "return context_data.join" in lines[j]:
                    saw_return = True
                if saw_return and lines[j].rstrip("\r\n") == "}":
                    break
                j += 1
            i = j + 1
            if i < len(lines) and not lines[i].strip():
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return "".join(out)


def clean_jsx(text: str) -> str:
    """Turn <TypesafeExample .../> JSX blocks into readable fenced JS blocks."""
    def repl(m: re.Match) -> str:
        body = m.group(1).strip()
        body = re.sub(r'^title="[^"]*"\s*', "", body)
        body = re.sub(r'^display="[^"]*"\s*', "", body)
        body = re.sub(r"^example=\{\{", "example = {", body, count=1)
        body = re.sub(r"\}\}\s*$", "}", body)
        return "```js example\n" + body.strip() + "\n```"

    return JSX_RE.sub(repl, text)


def clean_base(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = DOC_INDEX_RE.sub("", text)
    text = strip_example_component(text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip() + "\n"


def clean_text(text: str) -> str:
    return clean_jsx(clean_base(text))


def detect_function_type(text: str) -> str:
    """Pick the dominant TypeSafe primitive referenced in a block of text."""
    low = text.lower()
    scores = {
        "choice": (
            low.count("choice") * 3
            + low.count("option") * 1
            + low.count("classif") * 1
            + low.count("rout") * 1
            + low.count('"type": "choice"') * 4
        ),
        "noul": (
            low.count("noul") * 3
            + low.count("yes/no") * 2
            + low.count("yes or no") * 2
            + low.count("true or false") * 2
            + low.count('"type": "noul"') * 4
        ),
        "score": (
            low.count("score") * 3
            + low.count("rubric") * 2
            + low.count("level") * 1
            + low.count("spectrum") * 2
            + low.count('"type": "score"') * 4
        ),
    }
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "noul"


def doc_default_type(rel: str, title: str, body: str) -> str:
    hay = f"{rel} {title}".lower()
    for t in FUNCTION_TYPES:
        if t in hay:
            return t
    return detect_function_type(body)


def extract_tags(section: str, function_type: str, doc_title: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", section)
    counts: dict[str, int] = {}
    for w in words:
        lw = w.lower()
        if lw in STOPWORDS:
            continue
        counts[lw] = counts.get(lw, 0) + 1
    ranked = sorted(counts, key=lambda w: (-counts[w], w))[:8]
    base = ["typesafe", "jev", "system-one", function_type]
    seen: list[str] = []
    for tag in base + ranked:
        if tag not in seen:
            seen.append(tag)
    return seen[:10]


def parse_json_block(block: str):
    try:
        return json.loads(block)
    except Exception:
        return None


class JSParser:
    """Tolerant parser for the JS object literals used in docs examples."""

    def __init__(self, s: str):
        self.s = s
        self.i = 0

    def ws(self) -> None:
        while self.i < len(self.s) and self.s[self.i] in " \t\r\n":
            self.i += 1

    def peek(self) -> str:
        return self.s[self.i] if self.i < len(self.s) else ""

    def parse(self):
        self.ws()
        return self.value()

    def value(self):
        self.ws()
        c = self.peek()
        if c == "{":
            return self.obj()
        if c == "[":
            return self.arr()
        if c in "'\"":
            return self.string()
        if c == "-" or c.isdigit():
            return self.number()
        return self.ident()

    def ident(self):
        m = re.match(r"[A-Za-z_$][\w$]*", self.s[self.i:])
        if not m:
            raise ValueError(f"bad token at {self.i}: {self.s[self.i:self.i + 20]!r}")
        w = m.group(0)
        self.i += len(w)
        if w == "true":
            return True
        if w == "false":
            return False
        if w in ("null", "undefined", "NaN"):
            return None
        return w

    def string(self) -> str:
        q = self.s[self.i]
        self.i += 1
        out: list[str] = []
        mapping = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "f": "\f",
                   "/": "/", "\\": "\\", "'": "'", '"': '"'}
        while self.i < len(self.s):
            ch = self.s[self.i]
            if ch == "\\":
                self.i += 1
                out.append(mapping.get(self.s[self.i], self.s[self.i]))
                self.i += 1
            elif ch == q:
                self.i += 1
                break
            else:
                out.append(ch)
                self.i += 1
        return "".join(out)

    def number(self):
        m = re.match(r"-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", self.s[self.i:])
        w = m.group(0)
        self.i += len(w)
        if "." in w or "e" in w or "E" in w:
            return float(w)
        return int(w)

    def obj(self):
        self.i += 1
        d: dict = {}
        self.ws()
        if self.peek() == "}":
            self.i += 1
            return d
        while True:
            self.ws()
            if self.peek() == "}":
                self.i += 1
                break
            if self.peek() in "'\"":
                k = self.string()
            else:
                m = re.match(r"[\w$]+", self.s[self.i:])
                if not m:
                    raise ValueError("bad object key")
                k = m.group(0)
                self.i += len(k)
            self.ws()
            if self.peek() == ":":
                self.i += 1
            self.ws()
            d[k] = self.value()
            self.ws()
            if self.peek() == ",":
                self.i += 1
                continue
            if self.peek() == "}":
                self.i += 1
                break
            raise ValueError("bad object")
        return d

    def arr(self):
        self.i += 1
        a: list = []
        self.ws()
        if self.peek() == "]":
            self.i += 1
            return a
        while True:
            self.ws()
            if self.peek() == "]":
                self.i += 1
                break
            a.append(self.value())
            self.ws()
            if self.peek() == ",":
                self.i += 1
                continue
            if self.peek() == "]":
                self.i += 1
                break
            raise ValueError("bad array")
        return a


def parse_js_example(block: str):
    m = re.search(r"example=\{\{", block)
    if not m:
        return None
    inner = block[m.end():]
    k = inner.rfind("}}")
    if k != -1:
        inner = inner[:k]
    try:
        return JSParser("{" + inner + "}").parse()
    except Exception:
        return None


def extract_typed_examples(text: str) -> list[dict]:
    """Pair each JSX example that carries questions with a later answers fence."""
    requests = []
    for m in JSX_RE.finditer(text):
        obj = parse_js_example(m.group(1))
        if isinstance(obj, dict) and isinstance(obj.get("questions"), dict):
            requests.append({"offset": m.start(), "request": obj, "response": None})

    answers = []
    for m in JSON_FENCE_RE.finditer(text):
        obj = parse_json_block(m.group(1))
        if isinstance(obj, dict) and isinstance(obj.get("answers"), dict):
            answers.append({"offset": m.start(), "obj": obj})

    for req in requests:
        for a in answers:
            if a["offset"] > req["offset"]:
                req["response"] = a["obj"]
                break
    return requests


def split_sections(text: str) -> list[dict]:
    heads: list[tuple[int, int, str]] = []
    pos = 0
    fence = ""
    for line in text.split("\n"):
        stripped = line.lstrip()
        if fence:
            if stripped.startswith(fence):
                fence = ""
        elif stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
        else:
            m = HEAD_RE.match(stripped)
            if m:
                indent = len(line) - len(stripped)
                heads.append((pos + indent, len(m.group(1)), m.group(2).strip()))
        pos += len(line) + 1
    if not heads:
        return [{"level": 0, "heading": "", "body": text.strip(),
                 "start": 0, "end": len(text)}]
    sections: list[dict] = []
    if heads[0][0] > 0:
        pre = text[: heads[0][0]].strip()
        if pre:
            sections.append({"level": 0, "heading": "", "body": pre,
                             "start": 0, "end": heads[0][0]})
    for k, (pos, lvl, head) in enumerate(heads):
        end = heads[k + 1][0] if k + 1 < len(heads) else len(text)
        sections.append({"level": lvl, "heading": head, "body": text[pos:end].strip(),
                         "start": pos, "end": end})
    return sections


def iter_source_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXT:
            continue
        rel_parts = path.relative_to(ROOT).parts
        if any(p in SKIP_DIRS or p.startswith(".") for p in rel_parts[:-1]):
            continue
        if path.parent == ROOT and path.name in SKIP_FILES:
            continue
        yield path


def main() -> None:
    if RAW_DIR.exists():
        shutil.rmtree(RAW_DIR)
    RAW_DIR.mkdir(exist_ok=True)
    BUILD_DIR.mkdir(exist_ok=True)

    rows: list[dict] = []
    manifest: list[dict] = []
    seen_hashes: dict[str, str] = {}
    next_id = 0

    for path in iter_source_files():
        rel = path.relative_to(ROOT).as_posix()
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            original = path.read_text(encoding="utf-8", errors="ignore")

        base = clean_base(original)
        cleaned = clean_text(original)
        digest = sha256(cleaned)

        raw_path = RAW_DIR / rel
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(cleaned, encoding="utf-8")

        sections = split_sections(base)
        title_match = re.search(r"^#\s+(.+)$", cleaned, re.M)
        doc_title = title_match.group(1).strip() if title_match else path.stem
        summary_match = re.search(r"^>\s+(.+)$", cleaned, re.M)
        doc_summary = summary_match.group(1).strip() if summary_match else ""
        default_type = doc_default_type(rel, doc_title, cleaned)

        duplicate = digest in seen_hashes
        manifest.append({
            "source_path": rel,
            "raw_path": raw_path.relative_to(ROOT).as_posix(),
            "title": doc_title,
            "summary": doc_summary,
            "sha256": digest,
            "bytes": len(cleaned.encode("utf-8")),
            "sections": len(sections),
            "function_type": default_type,
            "duplicate_of": seen_hashes.get(digest) if duplicate else None,
        })

        if duplicate:
            continue
        seen_hashes[digest] = rel

        category = rel.split("/")[0] if "/" in rel else "root"
        typed = [e for e in extract_typed_examples(base)]
        for e in typed:
            e["section"] = None
            for sec in sections:
                if sec["start"] <= e["offset"] < sec["end"]:
                    e["section"] = sec
                    break

        for ex in typed:
            sec = ex["section"] or {"heading": "", "body": ""}
            heading = sec["heading"]
            body = sec["body"]
            request = ex["request"]
            response = ex["response"] or {}
            state = request.get("state", "")
            answers = response.get("answers", {})

            ftype = default_type
            qtypes = {
                q.get("type")
                for q in request.get("questions", {}).values()
                if isinstance(q, dict)
            }
            if qtypes:
                for cand in FUNCTION_TYPES:
                    if cand in qtypes:
                        ftype = cand
                        break
            elif heading:
                ftype = detect_function_type(f"{heading}\n{body}")

            label = {"choice": "Choice", "noul": "Noul", "score": "Score"}[ftype]
            questions = request.get("questions", {}) or {}
            has_answers = bool(answers)
            if has_answers:
                if heading:
                    instruction = (
                        f"Given the state, define and answer the TypeSafe System One "
                        f"{label} question(s) for '{heading}'."
                    )
                else:
                    instruction = (
                        f"Given the state, define and answer the TypeSafe System One "
                        f"{label} question(s) shown in {doc_title}."
                    )
                output = json.dumps(answers, ensure_ascii=False)
            else:
                if heading:
                    instruction = (
                        f"Define the TypeSafe System One {label} question(s) used for "
                        f"'{heading}'."
                    )
                else:
                    instruction = (
                        f"Define the TypeSafe System One {label} question(s) shown in "
                        f"{doc_title}."
                    )
                output = json.dumps(questions, ensure_ascii=False)
            rows.append({
                "id": next_id + 1,
                "dataset": DATASET_NAME,
                "instruction": instruction,
                "input": state if isinstance(state, str) else json.dumps(state, ensure_ascii=False),
                "output": output,
                "state": state,
                "question_block": questions,
                "answer_block": answers or None,
                "question_count": len(questions),
                "has_answer": has_answers,
                "model": response.get("model", request.get("model", "jev-latest")),
                "function_type": ftype,
                "doc_title": doc_title,
                "section": heading or doc_title,
                "category": category,
                "source": rel,
                "tags": extract_tags(f"{heading} {body}", ftype, doc_title),
                "credit": CREDIT,
            })
            next_id += 1

        example_sections = {id(e["section"]) for e in typed if e["section"]}

        for sec in sections:
            if id(sec) in example_sections:
                continue
            if category in SKIP_GENERIC_CATEGORIES:
                continue
            heading = sec["heading"]
            body = sec["body"]
            body_out = clean_jsx(body)
            if not heading and len(body) < 40:
                continue

            ftype = detect_function_type(f"{heading}\n{body}") if heading else default_type
            label = {"choice": "Choice", "noul": "Noul", "score": "Score"}[ftype]
            input_ctx = doc_summary or doc_title

            if heading:
                instruction = (
                    f"Explain '{heading}' from the TypeSafe AI {label} documentation "
                    f"for System One (Jev)."
                )
            else:
                instruction = f"Summarize {doc_title} from the TypeSafe AI System One documentation."
            rows.append({
                "id": next_id + 1,
                "dataset": DATASET_NAME,
                "instruction": instruction,
                "input": input_ctx,
                "output": body_out,
                "state": None,
                "question_block": None,
                "answer_block": None,
                "question_count": 0,
                "has_answer": False,
                "model": "jev-latest",
                "function_type": ftype,
                "doc_title": doc_title,
                "section": heading or doc_title,
                "category": category,
                "source": rel,
                "tags": extract_tags(f"{heading} {body}", ftype, doc_title),
                "credit": CREDIT,
            })
            next_id += 1

    (RAW_DIR / "manifest.json").write_text(
        json.dumps({
            "dataset": DATASET_NAME,
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "source": SOURCE_NAME,
            "credit": CREDIT,
            "credit_note": CREDIT_NOTE,
            "function_types": list(FUNCTION_TYPES),
            "file_count": len(manifest),
            "unique_file_count": sum(1 for m in manifest if not m["duplicate_of"]),
            "files": manifest,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Add SEO / AEO / GEO knowledge rows for MCP users
    seo_rows = [
        {
            "instruction": "Explain SEO (Search Engine Optimization) for AI agent MCP servers.",
            "input": "SEO for MCP servers",
            "output": "SEO for MCP servers involves optimizing landing pages, metadata, and content to rank in search engines. Key techniques: semantic HTML with heading hierarchy, descriptive meta tags (title, description, keywords), structured data (JSON-LD SoftwareApplication schema), fast edge caching via Cloudflare Workers, mobile-responsive design with safe-area-insets, and content matching user search intent. For DGUI-HyperMem: semantic <section> elements, aria labels, alt text on logos, structured data for software schema.",
            "state": {"topic": "SEO", "context": "MCP server optimization"},
            "question_block": None, "answer_block": None, "question_count": 0, "has_answer": False,
            "model": "jev-latest", "function_type": "choice", "doc_title": "SEO/AEO/GEO Knowledge",
            "section": "Search Engine Optimization", "category": "knowledge",
            "source": "built-in", "tags": ["seo", "search-engine", "discovery", "landing-page"],
            "credit": CREDIT, "credit_note": CREDIT_NOTE,
        },
        {
            "instruction": "Explain AEO (Answer Engine Optimization) for AI agent discovery.",
            "input": "AEO for AI agents",
            "output": "AEO structures content so AI answer engines (Google SGE, Bing Chat, Perplexity, Claude, ChatGPT) extract and surface it directly. For MCP servers: (1) Provide clear service descriptions in natural language, (2) Use JSON-LD SoftwareApplication schema, (3) Maintain an llms.txt file for AI crawlers, (4) Write AGENTS.md for coding agents, (5) Answer common questions directly in documentation. Our landing page states 'a self-hosted hybrid memory MCP server for AI agents with JEV reasoning' which directly answers discovery queries.",
            "state": {"topic": "AEO", "context": "AI agent discovery optimization"},
            "question_block": None, "answer_block": None, "question_count": 0, "has_answer": False,
            "model": "jev-latest", "function_type": "choice", "doc_title": "SEO/AEO/GEO Knowledge",
            "section": "Answer Engine Optimization", "category": "knowledge",
            "source": "built-in", "tags": ["aeo", "answer-engine", "ai-discovery", "llms-txt"],
            "credit": CREDIT, "credit_note": CREDIT_NOTE,
        },
        {
            "instruction": "Explain GEO (Generative Engine Optimization) for AI agent marketplaces.",
            "input": "GEO for AI agents",
            "output": "GEO targets generative AI systems that synthesize answers from multiple sources. For MCP servers: (1) Being referenced in AI training corpora (INSTRUCT_JEV dataset on HuggingFace), (2) Listing MCP tools in agent skill marketplaces, (3) Building integrations with LangChain, Vercel AI SDK, opencode, (4) Maintaining GitHub repos with README, CONTRIBUTING, AGENTS.md for AI coding agents, (5) Getting mentioned in AI publications. ROI: each integration increases agent invocations, growing dataset size and JEV accuracy in a self-reinforcing flywheel.",
            "state": {"topic": "GEO", "context": "Generative engine optimization"},
            "question_block": None, "answer_block": None, "question_count": 0, "has_answer": False,
            "model": "jev-latest", "function_type": "score", "doc_title": "SEO/AEO/GEO Knowledge",
            "section": "Generative Engine Optimization", "category": "knowledge",
            "source": "built-in", "tags": ["geo", "generative-engine", "marketplace", "discovery", "roi"],
            "credit": CREDIT, "credit_note": CREDIT_NOTE,
        },
    ]
    for i, row in enumerate(seo_rows):
        row["id"] = next_id + 1 + i
    rows.extend(seo_rows)
    next_id += len(seo_rows)

    (BUILD_DIR / "train.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
        encoding="utf-8",
    )

    per_type: dict[str, int] = {}
    for t in FUNCTION_TYPES:
        subset = [r for r in rows if r["function_type"] == t]
        per_type[t] = len(subset)
        (BUILD_DIR / f"{t}.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in subset) + "\n",
            encoding="utf-8",
        )

    per_category: dict[str, int] = {}
    for r in rows:
        per_category[r["category"]] = per_category.get(r["category"], 0) + 1

    stats = {
        "rows": len(rows),
        "per_function_type": per_type,
        "per_category": dict(sorted(per_category.items())),
        "source_files": len(manifest),
        "unique_source_files": sum(1 for m in manifest if not m["duplicate_of"]),
        "duplicates_skipped": sum(1 for m in manifest if m["duplicate_of"]),
        "rows_with_question_block": sum(1 for r in rows if r["question_block"]),
        "rows_with_answers": sum(1 for r in rows if r["has_answer"]),
    }
    (BUILD_DIR / "stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    metadata = {
        "dataset": DATASET_NAME,
        "title": "INSTRUCT_JEV",
        "pretty_name": "INSTRUCT_JEV - TypeSafe AI Jev / System One Instruction Corpus",
        "description": (
            "INSTRUCT_JEV is an instruction corpus built from the TypeSafe AI "
            "documentation for Jev, the first System One model. Every row is an "
            "instruction / input / output example over the three TypeSafe question "
            "primitives - choice, noul and score. "
            + CREDIT_NOTE
        ),
        "attribution": {
            "credit": CREDIT,
            "note": CREDIT_NOTE,
            "source": SOURCE_NAME,
            "source_url": SOURCE_URL,
            "license": LICENSE,
        },
        "publisher": "DeckerGUI",
        "compiled_by": "DeckerGUI",
        "license": LICENSE,
        "version": VERSION,
        "function_types": list(FUNCTION_TYPES),
        "structure": (
            "Mirrors deckerGUI-jev_corpus_RAW; each row is tagged with one of the "
            "three TypeSafe System One function types."
        ),
        "generated_from": RAW_DIR.name,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repo": REPO,
        "stats": stats,
        "schema": {
            "id": "int - sequential row id",
            "dataset": "string - INSTRUCT_JEV",
            "instruction": "string - the task / question",
            "input": "string - context or state",
            "output": "string or json - the expected answer",
            "state": "json or null - TypeSafe state when available",
            "question_block": "json or null - typed Choice/Noul/Score question objects",
            "answer_block": "json or null - typed answers",
            "question_count": "int - number of questions in the block",
            "has_answer": "bool - whether a typed answer block was extracted",
            "model": "string - model alias shown in docs (jev-latest)",
            "function_type": "string - choice | noul | score",
            "doc_title": "string",
            "section": "string",
            "category": "string",
            "source": "string - raw corpus relative path",
            "tags": "array",
            "credit": "string",
        },
        "integration": {
            "raw_corpus": RAW_DIR.name,
            "build_dir": BUILD_DIR.name,
        },
    }
    (BUILD_DIR / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    readme = f"""---
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

INSTRUCT_JEV is a **{PROJECT}** project and exists because of the work below.

| Who | Contribution | Link |
|-----|--------------|------|
| **TypeSafe AI** | Jev - the first System One model - and the Choice / Noul / Score primitives. Author of the documentation this corpus is built from. | <https://typesafe.ai> - <https://docs.typesafe.ai> |
| **DeckerGUI** | Compiled the corpus into instruction rows, published the dataset and tooling. | <{PROJECT_URL}> |
| **KrackedDevs** | Community credit and support. | KrackedDevs |
| **CTECX** | Knowledge / corpus partner. | CTECX |

All documentation, concepts, API design and examples are the work of **TypeSafe AI**
(<https://typesafe.ai>). Jev, System One and the Choice / Noul / Score primitives are
TypeSafe's. This corpus is compiled and redistributed under their MIT-licensed public
documentation at <{SOURCE_URL}>.

> {CREDIT_NOTE}
> Source: {SOURCE_NAME} - {SOURCE_URL}
> Compiled by **{PROJECT}**.

## Repository

Source, builder and raw mirror: <{GITHUB_REPO}>
HuggingFace dataset: <https://huggingface.co/datasets/{REPO}>

## Contributing

Contributions are welcome. See [CONTRIBUTING.md]({GITHUB_REPO}/blob/main/CONTRIBUTING.md)
and [CONTRIBUTORS.md]({GITHUB_REPO}/blob/main/CONTRIBUTORS.md) - contributors are added to
the credits table in the same pull request.

## Scope

The **RAW** mirror captures the full cleaned TypeSafe AI documentation corpus
(`deckerGUI-jev_corpus_RAW`, {stats['source_files']} files). The published instruction
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

- Rows: **{stats['rows']}**
- choice: **{per_type['choice']}** / noul: **{per_type['noul']}** / score: **{per_type['score']}**
- Rows with an extracted typed question block: **{stats['rows_with_question_block']}** (of which **{stats['rows_with_answers']}** include typed answers)
- Unique source documents: **{stats['unique_source_files']}** (from {stats['source_files']} captured files)

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
| `function_type` | string | `choice` \\| `noul` \\| `score` |
| `doc_title` | string | Source document title |
| `section` | string | Source section heading |
| `category` | string | Corpus category |
| `source` | string | Raw corpus relative path |
| `tags` | array | Search tags |
| `credit` | string | Attribution |

## Usage

```python
from datasets import load_dataset

dataset = load_dataset("{REPO}")
print(dataset["train"][0])
```

Per-primitive subsets are published alongside the full set: `choice.jsonl`,
`noul.jsonl`, `score.jsonl`.

## License

MIT (c) {PROJECT} - see [LICENSE]({GITHUB_REPO}/blob/main/LICENSE). Upstream TypeSafe AI
documentation is MIT-licensed; see their original terms at <{SOURCE_URL}>.
Compiled by {PROJECT} ({PROJECT_URL}).
"""
    (BUILD_DIR / "README.md").write_text(readme, encoding="utf-8")

    print(f"[ok] raw corpus    -> {RAW_DIR}  ({len(manifest)} files mirrored)")
    print(f"[ok] train.jsonl   -> {len(rows)} rows")
    print(f"[ok] per type      -> choice={per_type['choice']} noul={per_type['noul']} score={per_type['score']}")
    print(f"[ok] question block-> {stats['rows_with_question_block']} rows")
    print(f"[ok] duplicates    -> {stats['duplicates_skipped']} skipped")


if __name__ == "__main__":
    main()
