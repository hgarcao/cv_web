# Henery Garção — online CV and portfolio

Personal site: home, corporate CV, academic CV and a portfolio page with an interactive
hydrodynamic-model demo. Static HTML; no build step and no server.

- `index.html` — the CV: about, experience, research, projects, skills, education, interests (PDF versions for industry and academic submissions next to it)
- `portfolio.html` — two model demos, one below the other
- `demo/` — coastal currents viewer (Delft3D), see `demo/README.md`
- `demo-waves/` — Arabian Gulf wave viewer (SWAN), see `demo-waves/README.md`

Preview locally:

```bash
python -m http.server 8080
```

then open <http://localhost:8080/>.

Licence: MIT for the code (see `LICENSE`).
