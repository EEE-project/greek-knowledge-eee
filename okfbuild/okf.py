"""OKF (Open Knowledge Format) markdown serialization and disk I/O.

The single shared module every concept-type builder and the pipeline
orchestrator use to assemble a concept's frontmatter/body into OKF-format
markdown and write it to disk correctly.
"""

import re
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

import yaml

CONCEPT_TYPES = {"Lexical Entry", "Grammatical Rule", "Cultural Context"}

_COMMON_FIELDS = ("title", "description", "tags", "level", "sources", "generated", "status")

_FOOTNOTE_REF_RE = re.compile(r"\[\^([^\]]+)\]")


@dataclass
class Source:
    id: str
    resource: str
    title: str
    author: str


@dataclass
class ConceptFile:
    """In-memory representation of one OKF concept file, before serialization."""

    type: str
    title: str
    description: str
    tags: list[str]
    level: list[str]
    sources: list[Source]
    generated_by: str
    body: str  # already-formatted markdown body, footnotes included
    extra_frontmatter: dict  # type-specific fields (lemma/periods, periods_spanned, related_words/related_lessons)


def validate_frontmatter(frontmatter: dict) -> None:
    """Validate an assembled frontmatter dict against this project's OKF schema.

    Raises ValueError on any violation. Does not attempt live cross-reference
    checks (e.g. that related_words entries actually exist as files) — this
    is a shape/schema check only.
    """
    concept_type = frontmatter.get("type")
    if concept_type not in CONCEPT_TYPES:
        raise ValueError(f"type must be one of {sorted(CONCEPT_TYPES)}, got {concept_type!r}")

    for key in _COMMON_FIELDS:
        if key not in frontmatter:
            raise ValueError(f"missing required field: {key}")

    generated = frontmatter["generated"]
    if not isinstance(generated, dict) or "by" not in generated or "at" not in generated:
        raise ValueError("generated must be a mapping with 'by' and 'at' keys")

    level = frontmatter["level"]
    if not isinstance(level, list):
        raise ValueError(f"level must be a list, got {type(level).__name__}")

    if concept_type == "Lexical Entry":
        if "lemma" not in frontmatter or "periods" not in frontmatter:
            raise ValueError("Lexical Entry requires 'lemma' and 'periods'")
    elif concept_type == "Grammatical Rule":
        periods_spanned = frontmatter.get("periods_spanned")
        if not isinstance(periods_spanned, dict) or "from" not in periods_spanned or "to" not in periods_spanned:
            raise ValueError("Grammatical Rule requires periods_spanned as a {from, to} mapping, not a list")
    elif concept_type == "Cultural Context":
        if "related_words" not in frontmatter or "related_lessons" not in frontmatter:
            raise ValueError("Cultural Context requires 'related_words' and 'related_lessons'")


def render(concept: ConceptFile) -> str:
    """Serialize a ConceptFile into OKF-format markdown (YAML frontmatter + body)."""
    frontmatter = {
        "type": concept.type,
        "title": concept.title,
        "description": concept.description,
        "tags": concept.tags,
        "level": concept.level,
        "sources": [
            {"id": s.id, "resource": s.resource, "title": s.title, "author": s.author} for s in concept.sources
        ],
        "generated": {
            "by": concept.generated_by,
            "at": datetime.now(timezone.utc).isoformat(),
        },
    }
    frontmatter.update(concept.extra_frontmatter)
    frontmatter.setdefault("status", "draft")
    frontmatter.setdefault("verified", [])

    validate_frontmatter(frontmatter)

    yaml_text = yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)

    referenced_ids = set(_FOOTNOTE_REF_RE.findall(concept.body))
    footnote_lines = [
        f"[^{source.id}]: {source.title}, {source.author} ({source.resource})"
        for source in concept.sources
        if source.id in referenced_ids
    ]

    text = f"---\n{yaml_text}---\n{concept.body}"
    if footnote_lines:
        text += "\n\n" + "\n".join(footnote_lines) + "\n"
    return text


def _read_existing(path: Path) -> tuple[dict, str] | None:
    """Read and parse `path`'s frontmatter and body in one pass.

    Returns None if `path` doesn't exist, or exists but can't be parsed as
    OKF markdown (e.g. a human edit broke the `---` fence, or an unrelated
    file happens to sit in the same directory) — a bad existing file should
    never crash the caller, since this is exactly the file a human is most
    likely to have hand-edited.
    """
    if not path.exists():
        return None
    try:
        _, yaml_text, body = path.read_text().split("---\n", 2)
        return yaml.safe_load(yaml_text), body
    except (ValueError, yaml.YAMLError):
        return None


def _read_existing_frontmatter(path: Path) -> dict | None:
    """Read `path` and parse the YAML between its first two `---` lines into a dict."""
    existing = _read_existing(path)
    return existing[0] if existing is not None else None


def resolve_slug(out_dir: Path, slug: str, lemma: str, disambiguator: str | None = None) -> str:
    """Resolve the on-disk slug to actually use for `lemma`'s concept file in `out_dir`."""

    def _held_by_other_lemma(candidate_slug: str) -> bool:
        existing = _read_existing_frontmatter(out_dir / f"{candidate_slug}.md")
        return existing is not None and existing.get("lemma") != lemma

    if not _held_by_other_lemma(slug):
        return slug

    if disambiguator is not None:
        disambiguated = f"{slug}-{disambiguator}"
        if not _held_by_other_lemma(disambiguated):
            return disambiguated

    suffix = 2
    while True:
        candidate = f"{slug}-{suffix}"
        if not _held_by_other_lemma(candidate):
            return candidate
        suffix += 1


def _strip_generated_at(frontmatter: dict) -> dict:
    stripped = dict(frontmatter)
    generated = stripped.get("generated")
    if isinstance(generated, dict):
        stripped["generated"] = {k: v for k, v in generated.items() if k != "at"}
    return stripped


def write(concept: ConceptFile, path: Path) -> bool:
    """Write `concept` to `path`.

    Verification-preserving: if `path` already exists, its current
    `verified:` frontmatter list is merged into `concept` before rendering,
    so a human-added `verified` entry is never silently discarded by a
    later pipeline run.

    Idempotent on everything else: if the rendered content (including the
    merged `verified` list) is byte-identical to what's already on disk,
    ignoring only `generated.at`, the file is left untouched. Returns True
    if the file was written/changed, False if it was already up to date.
    """
    existing = _read_existing(path)

    if existing is not None:
        existing_frontmatter, existing_body = existing
        extra_frontmatter = dict(concept.extra_frontmatter)
        extra_frontmatter["verified"] = existing_frontmatter.get("verified", [])
        concept = replace(concept, extra_frontmatter=extra_frontmatter)

    rendered = render(concept)

    if existing is not None:
        _, rendered_yaml, rendered_body = rendered.split("---\n", 2)
        rendered_frontmatter = yaml.safe_load(rendered_yaml)
        if (
            _strip_generated_at(existing_frontmatter) == _strip_generated_at(rendered_frontmatter)
            and existing_body == rendered_body
        ):
            return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered)
    return True
