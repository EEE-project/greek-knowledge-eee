"""Minimal example: wire a real SourceBundle and confirm it's ready.

    uv run python examples/wire_sources.py
"""

from pathlib import Path

from okfbuild.wiring import default_source_bundle

REPO_ROOT = Path(__file__).parent.parent

sources = default_source_bundle(REPO_ROOT)
print("SourceBundle wired from", REPO_ROOT)
print(f"  byzantine_forms: {len(sources.byzantine_forms)} lemmas (0 means no sibling greek-inflexion-eee checkout found)")
print(f"  iecor: {len(sources.iecor or {})} headwords")
