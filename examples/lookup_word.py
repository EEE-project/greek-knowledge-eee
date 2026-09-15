"""Look up one word across every lemma-keyed source and print what each found.

    uv run python examples/lookup_word.py <word> [pos]
"""

import sys
from pathlib import Path

from okfbuild.lookup import lookup_word
from okfbuild.wiring import default_source_bundle

REPO_ROOT = Path(__file__).parent.parent


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: uv run python examples/lookup_word.py <word> [pos]", file=sys.stderr)
        raise SystemExit(1)
    lemma = sys.argv[1]
    pos = sys.argv[2] if len(sys.argv) > 2 else "noun"

    sources = default_source_bundle(REPO_ROOT)
    results = lookup_word(lemma, sources, pos=pos)

    if not results:
        print(f"No source has anything for {lemma!r}.")
        return
    for source_name, result in results.items():
        print(f"\n== {source_name} ==")
        print(result)


if __name__ == "__main__":
    main()
