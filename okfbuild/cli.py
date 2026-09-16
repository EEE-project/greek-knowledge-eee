"""Command-line entry point (`greek-knowledge`, see pyproject.toml's
[project.scripts]) for this KB's sources -- lookup and build are
read-only exploration. regenerate is the one subcommand that writes to
this repo's tracked words/ content, and only with an explicit --write
flag (see _cmd_regenerate's docstring for why that matters); check
validates any committed concept file (words/, grammar/, culture/, texts/)
instead of generating it, and only writes with an explicit --fix flag
(see okfbuild/check.py). No other command in this codebase writes there -- in
particular, the test suite doesn't: tests/test_pilot_acceptance.py
validates a real pipeline.run() against a scratch directory, never the
real repo root, so `uv run pytest` (with or without -m flags) can never
change tracked content as a side effect.
"""

import argparse
import os
import sys
from pathlib import Path

from okfbuild.concepts import lexical_entry
from okfbuild.lookup import lookup_word
from okfbuild.query import LIST_FIELDS, TYPE_BY_DIR, find_concepts, list_mode_report
from okfbuild.wiring import default_source_bundle, full_source_bundle

_DEFAULT_PERIODS = ["homeric", "attic", "modern"]


def _repo_root() -> Path:
    return Path(__file__).parent.parent


def _cmd_lookup(args: argparse.Namespace) -> None:
    sources = default_source_bundle(_repo_root())
    results = lookup_word(args.word, sources, pos=args.pos)
    if not results:
        print(f"No source has anything for {args.word!r}.")
        return
    for source_name, result in results.items():
        print(f"\n== {source_name} ==")
        print(result)


def _cmd_build(args: argparse.Namespace) -> None:
    sources = default_source_bundle(_repo_root())
    periods = args.period or _DEFAULT_PERIODS
    concept = lexical_entry.build(args.word, args.pos, periods, sources, level=[], tags=[])
    if not concept.extra_frontmatter["periods"]:
        print(f"No attested data for {args.word!r} in any requested period/source.")
        return
    print(concept.body)


def _cmd_query(args: argparse.Namespace) -> None:
    raw = {field: getattr(args, field) for field in LIST_FIELDS}
    report = list_mode_report(_repo_root(), raw)
    if report is not None:
        for field, values in report.items():
            print(f"-- {field} --")
            for value, count in values:
                print(f"{value} ({count})")
        return

    concept_type = TYPE_BY_DIR.get(args.type) if args.type else None
    matches = find_concepts(
        _repo_root(),
        type=concept_type,
        level=args.level,
        period=args.period,
        dialect=args.dialect,
        author=args.author,
    )
    if not matches:
        print("No concepts match those filters.")
        return
    for path, concept in matches:
        if args.full:
            print(f"\n== {path.relative_to(_repo_root())} — {concept.title} ==")
            print(concept.body)
        else:
            print(f"{path.relative_to(_repo_root())}  —  {concept.title}")


def _cmd_check(args: argparse.Namespace) -> None:
    """Validates committed concept files (words/, grammar/, culture/,
    texts/ -- see okfbuild/check.py's module docstring) -- ruff-style: prints one line
    per problem and exits 1 if any are found, silently exits 0 if clean.
    With no path arguments, checks everything; given one or more file or
    directory arguments, scopes to just those. --fix mechanically
    re-renders each checked file that needs it (frontmatter shape,
    footnote-definitions block) and reports what's left afterward -- an
    unresolvable citation or a frontmatter schema violation still needs a
    human fix, never auto-applied."""
    from okfbuild import check

    repo_root = _repo_root()
    paths = check.resolve_targets(repo_root, args.paths)
    if args.fix:
        for path in paths:
            check.fix_file(path)

    issues = [issue for path in paths for issue in check.check_file(path)]
    for issue in issues:
        print(f"{issue.path.relative_to(repo_root)}: {issue.message}")
    if issues:
        raise SystemExit(1)


def _cmd_regenerate(args: argparse.Namespace) -> None:
    """Runs the real pipeline against the real Odyssey/Kavafis Ithaki
    course content, writing into this repo's own words/ in place -- the
    same run tests/test_pilot_acceptance.py's pilot_output_dir fixture
    exercises against a scratch directory instead. grammar/ and culture/
    are hand-authored, not touched here -- see `greek-knowledge check`.
    --write is mandatory, not a default-on flag with an opt-out: this is
    the one command in this codebase that can change tracked corpus
    content, so triggering it must always be a deliberate, explicit
    choice, never a default or a side effect of anything else (see the
    module docstring). Review the resulting `git diff` before committing,
    same as any other pilot regen."""
    if not args.write:
        print(
            "Refusing to regenerate without --write: this rewrites the real "
            "words/ content in this repo in place. "
            "Re-run with --write once you mean that.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    from okfbuild import pipeline
    from okfbuild.pilot_content import enrich_nostos_with_beekes

    repo_root = _repo_root()
    env_path = os.environ.get("CREATED_WITH_EEE_PATH")
    created_with_eee_root = Path(env_path) if env_path else repo_root.parent / "created_with_eee"
    if not created_with_eee_root.is_dir():
        print(f"created_with_eee checkout not found at {created_with_eee_root} (set CREATED_WITH_EEE_PATH)", file=sys.stderr)
        raise SystemExit(1)

    course_paths = [
        created_with_eee_root / "ancient_greek" / "odyssey",
        created_with_eee_root / "modern_greek" / "b1greeklanguageandculture" / "kavafis_ithaki",
    ]
    sources = full_source_bundle(repo_root)
    report = pipeline.run(course_paths, out_dir=repo_root, sources=sources)
    enrich_nostos_with_beekes(repo_root, sources)

    print(f"written={report.written} unchanged={report.unchanged} failed={report.failed}")
    for error in report.errors:
        print(f"  error: {error}", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(prog="greek-knowledge", description="Explore greek-knowledge-eee's sources.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lookup_parser = subparsers.add_parser("lookup", help="look up one word across every lemma-keyed source")
    lookup_parser.add_argument("word")
    lookup_parser.add_argument("--pos", default="noun")
    lookup_parser.set_defaults(func=_cmd_lookup)

    build_parser = subparsers.add_parser("build", help="build (without writing) one Lexical Entry and print its body")
    build_parser.add_argument("word")
    build_parser.add_argument("--pos", default="noun")
    build_parser.add_argument("--period", action="append", help="repeatable; default: homeric attic modern")
    build_parser.set_defaults(func=_cmd_build)

    regenerate_parser = subparsers.add_parser(
        "regenerate", help="regenerate words/ from the real pilot courses (writes to this repo; needs --write)"
    )
    regenerate_parser.add_argument("--write", action="store_true", help="required -- without it, refuses and exits 1")
    regenerate_parser.set_defaults(func=_cmd_regenerate)

    check_parser = subparsers.add_parser(
        "check", help="validate words/grammar/culture/texts content (exits 1 if any problems are found)"
    )
    check_parser.add_argument("paths", nargs="*", help="files or directories to check (default: everything)")
    check_parser.add_argument("--fix", action="store_true", help="mechanically re-render files that need it before reporting")
    check_parser.set_defaults(func=_cmd_check)

    query_parser = subparsers.add_parser("query", help="find committed grammar/culture/words/texts by level, period, dialect, author")
    query_parser.add_argument("--type", choices=sorted(TYPE_BY_DIR) + ["list"], help="restrict to one concept type; 'list' prints the values in use instead of querying")
    query_parser.add_argument("--level", help="pass 'list' to print the values in use instead of querying")
    query_parser.add_argument("--period", help="pass 'list' to print the values in use instead of querying")
    query_parser.add_argument("--dialect", help="pass 'list' to print the values in use instead of querying")
    query_parser.add_argument("--author", help="case-insensitive substring match against any source's author; pass 'list' to print the values in use instead of querying")
    query_parser.add_argument("--full", action="store_true", help="print full bodies instead of just paths+titles")
    query_parser.set_defaults(func=_cmd_query)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
