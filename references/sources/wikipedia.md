# Wikipedia

The Wikipedia REST API, `GET
https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}`, no auth
required, CC BY-SA content, used for Cultural Context entries.

Every request must set a descriptive `User-Agent` and back off/retry on
429/5xx responses (Wikimedia API etiquette) — only a 404 means "no such
page."

Client: `okfbuild/sources/wikipedia_client.py` (added in
section-03-source-clients).
