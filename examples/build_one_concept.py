"""Build (but don't write) one Lexical Entry and print its markdown body.

    uv run python examples/build_one_concept.py <word> [pos] [period ...]
"""

import sys
from pathlib import Path

from okfbuild.concepts import lexical_entry
from okfbuild.wiring import default_source_bundle

REPO_ROOT = Path(__file__).parent.parent
DEFAULT_PERIODS = ["homeric", "attic", "modern"]


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: uv run python examples/build_one_concept.py <word> [pos] [period ...]", file=sys.stderr)
        raise SystemExit(1)
    lemma = sys.argv[1]
    pos = sys.argv[2] if len(sys.argv) > 2 else "noun"
    periods = sys.argv[3:] or DEFAULT_PERIODS

    sources = default_source_bundle(REPO_ROOT)
    concept = lexical_entry.build(lemma, pos, periods, sources, level=[], tags=[])

    if not concept.extra_frontmatter["periods"]:
        print(f"No attested data for {lemma!r} in any requested period/source.")
        return
    print(concept.body)


if __name__ == "__main__":
    main()
