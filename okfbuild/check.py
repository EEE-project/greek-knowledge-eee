"""Checks that any committed OKF concept file is well-formed markdown:
parseable frontmatter, every citation resolvable in both directions, and
canonically rendered (the footnote-definitions block matches sources: and
what's actually cited in the body). Unlike okfbuild/pipeline.py, this
never invents body prose -- it only verifies (and, via fix_file(),
mechanically re-renders) the parts okf.render() already derives from
what's written: YAML frontmatter shape and the footnote-definitions
block. words/ is pipeline-generated, so it's already guaranteed to be
well-formed at generation time -- but a human can and does hand-correct
one afterward, so it's checked here the same as everything else; see
templates/ for the expected shape of a new hand-authored file.

A file's `verified:` records are checked too (see record_verification()):
each must be well-formed, and at least one must be pinned to the file's
current text, so a rule edited after its review is reported as stale.
"""

import re
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path

import yaml

from okfbuild import okf

_CHECKED_DIRS = ("words", "grammar", "culture", "texts")

_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}")

# Lexical Entry/Grammatical Rule/Cultural Context prose makes claims and
# cites sources inline via [^id] -- every declared source should be used
# and every citation should resolve. Literary Translation's and Literary
# Text's sources: list is plain provenance for the whole passage (where the
# text came from), not a set of claims to cite piecemeal -- the body is the
# text itself, normally with no [^id] markers at all, so neither direction
# applies.
_TYPES_REQUIRING_INLINE_CITATIONS = {"Lexical Entry", "Grammatical Rule", "Cultural Context"}


@dataclass
class Issue:
    path: Path
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.message}"


def _unparseable(path: Path) -> Issue:
    return Issue(path, "cannot parse as OKF markdown, or missing a required common field")


def check_file(path: Path) -> list[Issue]:
    """Check one concept file for internal consistency and for a sound,
    current verification record. Returns a list of Issues (empty if the
    file is well-formed)."""
    concept = okf.read(path)
    if concept is None:
        return [_unparseable(path)]
    return _structure_issues(path, concept) + _verification_issues(path, concept)


def check_structure(path: Path) -> list[Issue]:
    """The structural checks of check_file() alone -- frontmatter shape,
    citations, canonical rendering -- without judging the file's
    verification record (a record left stale by an edit is exactly what
    record_verification() is about to replace)."""
    concept = okf.read(path)
    if concept is None:
        return [_unparseable(path)]
    return _structure_issues(path, concept)


def _verified_entry_problem(entry) -> str | None:
    """Why one `verified:` entry is malformed, or None if it is well-formed."""
    if not isinstance(entry, dict):
        return "is not a mapping"
    missing = [key for key in ("by", "at", "against", "body_sha256") if key not in entry]
    if missing:
        return f"is missing {', '.join(missing)}"
    if not isinstance(entry["by"], str) or not entry["by"].strip():
        return "needs a non-empty by"
    if not _DATE_RE.fullmatch(str(entry["at"])):
        return "needs at as a YYYY-MM-DD date"
    against = entry["against"]
    if not isinstance(against, list) or not against or not all(isinstance(item, str) and item.strip() for item in against):
        return "needs against as a non-empty list of text"
    if not isinstance(entry["body_sha256"], str) or not _DIGEST_RE.fullmatch(entry["body_sha256"]):
        return "needs body_sha256 as 64 hex characters"
    return None


def _verification_issues(path: Path, concept: okf.ConceptFile) -> list[Issue]:
    if not isinstance(concept.verified, list) or not concept.verified:
        return []  # nothing recorded (a non-list is already reported as invalid frontmatter)

    issues = [
        Issue(path, f"verified entry {number} {problem}")
        for number, entry in enumerate(concept.verified, start=1)
        if (problem := _verified_entry_problem(entry))
    ]
    if not issues and okf.current_verification(concept) is None:
        issues.append(
            Issue(path, "verified record is stale: the text changed after it was verified (re-check it, then run greek-knowledge verify)")
        )
    return issues


def _structure_issues(path: Path, concept: okf.ConceptFile) -> list[Issue]:
    issues: list[Issue] = []
    referenced_ids = okf.referenced_footnote_ids(concept.body)
    source_ids = {s.id for s in concept.sources}

    if concept.type in _TYPES_REQUIRING_INLINE_CITATIONS:
        for missing in sorted(referenced_ids - source_ids):
            issues.append(Issue(path, f"footnote [^{missing}] is cited in the body but has no matching sources: entry"))
        for unused in sorted(source_ids - referenced_ids):
            issues.append(Issue(path, f"sources: entry {unused!r} is never cited as [^{unused}] in the body"))

    try:
        rendered = okf.render(concept)
    except ValueError as exc:
        issues.append(Issue(path, f"invalid frontmatter: {exc}"))
        return issues

    raw = path.read_text(encoding="utf-8")
    _, existing_yaml, existing_body = raw.split("---\n", 2)
    _, rendered_yaml, rendered_body = rendered.split("---\n", 2)
    existing_fm = yaml.safe_load(existing_yaml)
    rendered_fm = yaml.safe_load(rendered_yaml)
    for fm in (existing_fm, rendered_fm):
        generated = fm.get("generated")
        if isinstance(generated, dict):
            generated.pop("at", None)
    if existing_fm != rendered_fm:
        issues.append(Issue(path, "frontmatter doesn't match its canonical rendering (run check --fix)"))
    # Trailing newlines aren't content: an editor may add or drop the final one freely.
    if existing_body.rstrip("\n") != rendered_body.rstrip("\n"):
        issues.append(Issue(path, "footnote-definitions block doesn't match sources: (run check --fix)"))

    return issues


def _concept_files_under(dirpath: Path) -> list[Path]:
    """Every *.md file under dirpath (recursively), except index.md."""
    return sorted(p for p in dirpath.rglob("*.md") if p.name != "index.md")


def iter_checked_files(repo_root: Path) -> list[Path]:
    """Every hand-authored concept file under grammar/, culture/, and
    texts/ (recursively, for texts/<work>/*.md) -- words/ is
    pipeline-generated and out of scope, see the module docstring."""
    return [path for dirname in _CHECKED_DIRS for path in _concept_files_under(repo_root / dirname)]


def resolve_targets(repo_root: Path, paths: list[str]) -> list[Path]:
    """Resolve CLI path arguments to concept files to check: a directory
    is walked the same way iter_checked_files() walks each of
    _CHECKED_DIRS (recursively, skipping index.md); a file is used as-is,
    whether or not it lives under one of those directories. Empty `paths`
    means check everything -- see iter_checked_files()."""
    if not paths:
        return iter_checked_files(repo_root)

    targets: list[Path] = []
    for raw in paths:
        path = Path(raw).resolve()
        targets.extend(_concept_files_under(path) if path.is_dir() else [path])
    return targets


def check_corpus(repo_root: Path) -> list[Issue]:
    """Check every file iter_checked_files() finds."""
    issues: list[Issue] = []
    for path in iter_checked_files(repo_root):
        issues.extend(check_file(path))
    return issues


def fix_file(path: Path) -> bool:
    """Mechanically re-render `path` to its canonical OKF form (matching
    the footnote-definitions block to sources: and what's cited,
    normalizing frontmatter shape). Never touches body prose or the
    sources/citations themselves -- an unresolvable [^id], an uncited
    sources: entry, or a frontmatter schema violation all need a human
    decision, not a mechanical rewrite; check_file() still reports those
    after fixing. Returns True if the file changed."""
    concept = okf.read(path)
    if concept is None:
        return False
    return okf.write(concept, path)


def record_verification(path: Path, *, by: str, against: list[str], on: date | None = None) -> list[Issue]:
    """Pin a verification record -- who checked the rule (`by`), on what
    date, against what (`against`) -- to the text `path` has right now,
    replacing any earlier record. Returns the structural Issues that stopped
    it, in which case nothing is written: a file that is not well-formed
    cannot be vouched for. Editing the text afterwards makes the record
    stale, which check_file() reports and query's `verified` filter ignores."""
    concept = okf.read(path)
    if concept is None:
        return [_unparseable(path)]
    issues = _structure_issues(path, concept)
    if issues:
        return issues

    entry = {
        "by": by,
        "at": (on or date.today()).isoformat(),
        "against": list(against),
        "body_sha256": okf.body_digest(concept.body),
    }
    if problem := _verified_entry_problem(entry):
        raise ValueError(f"cannot record a verification: it {problem}")
    path.write_text(okf.render(replace(concept, verified=[entry])), encoding="utf-8")
    return []
