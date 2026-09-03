# data/lsj/

Perseus LSJ (Liddell-Scott-Jones) TEI-XML files — one-time, **local-only**
downloads, gitignored (`*.xml` here is never committed; see `.gitignore`).
Only the headwords actually looked up during a build get resolved and
cached, as small per-headword JSON files under `../lsj-cache/` (git-tracked,
plain — not LFS, same pattern `../morpheus-cache/` and
`../wiktextract-cache/` already use). Once a headword's answer is cached, a
rebuild doesn't need these files present at all, so this directory can be
safely deleted after a build without losing anything already resolved —
only re-download when a genuinely new headword needs resolving
(`CachedLSJIndex` logs a warning in that case rather than failing outright,
since LSJ is enrichment, not a hard requirement).

Source: https://github.com/PerseusDL/lexica/tree/master/CTS_XML_TEI/perseus/pdllex/grc/lsj
(27 files, `grc.lsj.perseus-eng[1-27].xml`, ~270MB total). CC BY-SA 4.0 —
attribution to Perseus required.
