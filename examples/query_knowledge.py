"""Minimal example: find committed grammar/culture/words/texts entries by
level, period, dialect, or author. Same as `greek-knowledge query`, as a
script — see okfbuild/query.py's find_concepts() for the underlying API.

Usage:
    uv run python examples/query_knowledge.py --level beginner --dialect attic
    uv run python examples/query_knowledge.py --level list
"""

import argparse
from pathlib import Path

from okfbuild.query import LIST_FIELDS, TYPE_BY_DIR, find_concepts, list_mode_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=sorted(TYPE_BY_DIR) + ["list"], help="pass 'list' to print the values in use instead of querying")
    parser.add_argument("--level", help="pass 'list' to print the values in use instead of querying")
    parser.add_argument("--period", help="pass 'list' to print the values in use instead of querying")
    parser.add_argument("--dialect", help="pass 'list' to print the values in use instead of querying")
    parser.add_argument("--author", help="pass 'list' to print the values in use instead of querying")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    raw = {field: getattr(args, field) for field in LIST_FIELDS}
    report = list_mode_report(repo_root, raw)
    if report is not None:
        for field, values in report.items():
            print(f"-- {field} --")
            for value, count in values:
                print(f"{value} ({count})")
        return

    matches = find_concepts(
        repo_root,
        type=TYPE_BY_DIR.get(args.type) if args.type else None,
        level=args.level,
        period=args.period,
        dialect=args.dialect,
        author=args.author,
    )
    if not matches:
        print("No concepts match those filters.")
        return
    for path, concept in matches:
        print(f"{path.relative_to(repo_root)}  —  {concept.title}")


if __name__ == "__main__":
    main()
