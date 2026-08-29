# Diagrams

The seven diagrams in `magic-robots-protocol.md` are generated, not drawn. Sources are in
`diagrams/*.dot`; rendered SVGs land in `img/` and are what the document references.

Regenerate after editing a source:

```sh
cd docs/protocol/diagrams
for f in *.dot; do dot -Tsvg "$f" -o "../img/${f%.dot}.svg"; done
```

Needs graphviz (`brew install graphviz`).

## Conventions

The SVGs are rendered with `bgcolor="transparent"` and every node carries its own light fill with
dark text, so they stay legible on both light and dark backgrounds. Edges and edge labels are
`#888888`, which reads on either. **Do not add an opaque background** — it breaks dark mode.

Palette, by meaning:

| Colour | Meaning |
|---|---|
| `#cfe3f7` blue | control plane: HTTP routes, match-boundary events |
| `#d8ecd8` green | the event stream and turn-level events |
| `#f7e3c0` amber | server-side state: the arena, the registry, health |
| `#f6cfcf` red | failure, death, and the paths a client gets wrong |
| `#e6e6e6` grey | decisions, notes, and everything neutral |
