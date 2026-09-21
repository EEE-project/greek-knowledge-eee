"""Minimal example: find committed grammar/culture/words/texts entries by
level, period, dialect, author, work, or language (--verified: only those whose current text has a
verification record). Same as `greek-knowledge query`, as a
script — see okfbuild/query.py's find_concepts() for the underlying API.

Usage:
    uv run python examples/query_knowledge.py --level beginner --dialect attic
    uv run python examples/query_knowledge.py --period homeric..attic --language el,grc
    uv run python examples/query_knowledge.py --level list
    uv run python examples/query_knowledge.py --type grammar --period modern --verified
"""

import argparse
from pathlib import Path

from okfbuild.query import LIST_FIELDS, add_filter_arguments, concept_types, find_concepts, list_mode_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    add_filter_arguments(parser)
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    raw = {field: getattr(args, field) for field in LIST_FIELDS}
    report = list_mode_report(repo_root, raw, verified=args.verified)
    if report is not None:
        for field, values in report.items():
            print(f"-- {field} --")
            for value, count in values:
                print(f"{value} ({count})")
        return

    matches = find_concepts(
        repo_root,
        type=concept_types(args.type),
        level=args.level,
        period=args.period,
        dialect=args.dialect,
        author=args.author,
        work=args.work,
        language=args.language,
        verified=args.verified,
    )
    if not matches:
        print("No concepts match those filters.")
        return
    for path, concept in matches:
        print(f"{path.relative_to(repo_root)}  —  {concept.title}")


if __name__ == "__main__":
    main()
