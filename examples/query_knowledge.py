"""Minimal example: find committed grammar/culture/words/texts entries by
level, period, dialect, or author. Same as `greek-knowledge query`, as a
script — see okfbuild/query.py's find_concepts() for the underlying API.

Usage:
    uv run python examples/query_knowledge.py --level beginner --dialect attic
"""

import argparse
from pathlib import Path

from okfbuild.query import find_concepts

_TYPE_SHORTHAND = {
    "words": "Lexical Entry",
    "grammar": "Grammatical Rule",
    "culture": "Cultural Context",
    "texts": "Literary Translation",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--type", choices=sorted(_TYPE_SHORTHAND))
    parser.add_argument("--level")
    parser.add_argument("--period")
    parser.add_argument("--dialect")
    parser.add_argument("--author")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    matches = find_concepts(
        repo_root,
        type=_TYPE_SHORTHAND.get(args.type) if args.type else None,
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
