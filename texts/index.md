# Literary Text and Literary Translation entries

One subdirectory per literary work, each with its own `index.md`. Hand-
authored, not built by `okfbuild/pipeline.py` — there is no live source to
query for a human translation, and no generator step at all: copy
[`templates/literary-text.md`](../templates/literary-text.md) for a work's
original or [`templates/literary-translation.md`](../templates/literary-translation.md)
for a translation, fill it in, and run `uv run greek-knowledge check` to
validate it.
`kavafis_ithaki/` is authored this way already; `odyssey/` still has its
own one-off script (`scripts/populate_odyssey_texts.py`) with the text
hardcoded as Python constants, not yet migrated to hand-authored files.

- [odyssey/](odyssey/index.md) — Homer's Odyssey (I.1-21, IX.19-38)
- [kavafis_ithaki/](kavafis_ithaki/index.md) — Cavafy's «Ithaka» (the complete poem, 36 lines)

## Reading a work

Each work's directory holds `text.md` (the original, a Literary Text) and one `translations_<lang>.md` per
language (Literary Translations: one `##` section per translator; a "reference only" section carries a
link but no text). From the repo root:

```bash
uv run greek-knowledge query --type texts --work list                           # which works there are
uv run greek-knowledge query --type texts --work ithaka --language ru --full    # Ithaka, every Russian version
uv run greek-knowledge query --type texts --work ithaka --language ru,en --full # Russian and English together
uv run greek-knowledge query --type texts --work odyssey --language grc --full  # the Odyssey's Greek original
awk '/^## <translator>/{f=1;next} /^## /{f=0} f' texts/<work>/translations_<lang>.md   # one translator's section
sed '1,/^---$/d' texts/<work>/text.md | grep -v -E '^(#|<!--|$)'                        # just the verse lines
```

`query --type texts` spans originals and translations alike. `--work` is a case-insensitive substring of a
file's `work` frontmatter (`--work list` shows the values in use) and `--language` its exact language code
(`el`, `en`, `ru`, `grc`; `--language list` shows them). Every filter takes several values -- repeat the flag or
separate them with a comma, `--language ru,en` -- and a file matching any one is kept. `--author` only matches a
file's `sources:` authors, so it is a poor way to pick one work. `--full` prints the bodies without the frontmatter.
