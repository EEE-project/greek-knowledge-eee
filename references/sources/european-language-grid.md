# European Language Grid (ELG) catalogue

`https://live.european-language-grid.eu/catalogue/` — similar in kind to
CLARIN's Virtual Language Observatory (see
[[`references/sources/clarin-vlo.md`](clarin-vlo.md)](clarin-vlo.md)): a searchable
catalogue of language resources and language-technology tools, not a
single dataset. Part of the broader ELG platform, whose focus leans more
toward callable NLP services (translation, NER, and similar tools) than
raw linguistic datasets.

**Status: not integrated, same "discovery, not citation" role as
CLARIN VLO.** ELG's platform documents a REST API
(`european-language-grid.readthedocs.io`) for *running* language-
technology tool containers as callable services — but a
catalogue-search-specific API (for querying the resource listing itself,
as opposed to invoking a tool) was not confirmed from the pages checked.
Like CLARIN VLO, valuable as a discovery entry point rather than a
build-time dependency.
