# Henery Garção — online CV and portfolio

Personal site: home, corporate CV, academic CV and a portfolio page with an interactive
hydrodynamic-model demo. Static HTML; no build step and no server.

- `index.html` — home
- `corporate.html`, `academic.html` — the two CV versions (PDF downloads next to them)
- `portfolio.html` — portfolio page; embeds the demo
- `demo/` — coastal currents viewer (see `demo/README.md`)

Preview locally:

```bash
python -m http.server 8080
```

then open <http://localhost:8080/>.

Licence: MIT for the code (see `LICENSE`).
