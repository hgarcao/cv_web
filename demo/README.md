# Coastal Currents Demo — Vitória Bay, ES, Brazil

Interactive viewer for the output of a D-Flow FM (Delft3D Flexible Mesh) hydrodynamic model of
Vitória Bay and the adjacent Espírito Santo coast. It animates modelled currents (particles or
arrows), overlays ECMWF 10 m wind, and plots speed, direction and water level at a clicked point.

The demo is **static**: it reads pre-computed files from `data/`. It does not run the model and is
not a live forecast.

## Run locally

```bash
python -m http.server 8080
```

from the repository root (or from this folder), then open <http://localhost:8080/demo/>.
A browser with WebGL and `DecompressionStream` (any current Chrome, Edge, Firefox or Safari) is needed.

## Data

| File | Content |
|---|---|
| `data/meta.json` | time steps (217, every 20 min, 2026-06-10 00:00 to 2026-06-13 00:00 UTC), grid, coarse-cell coordinates |
| `data/mask.bin.gz` | land/water mask, 300 × 300, uint8 |
| `data/step_NNN.bin.gz` | current components u, v (int16, mm/s) on the 300 × 300 regular grid |
| `data/series.bin.gz` | u, v, water level on a coarser grid for all steps (click → time series) |
| `data/wind.json` | ECMWF 10 m wind; covers 2026-06-10 00:00–21:00 UTC only |
| `data/station.json` | **virtual** tide station with **synthetic** observations (model + seeded correlated noise) |

`tools/build_static_data.py` shows how these files were produced from the model output
(`merged_resultado.nc`, 395 MB, not included) with `tools/requirements.txt`.

## Notes and limitations

- Interpolation from the unstructured mesh to a regular grid smooths features smaller than one cell (about 70 m × 80 m).
- The tide station is virtual; its observations are synthetic and illustrative, not measurements.
- Base maps: CARTO and OpenStreetMap contributors. Libraries (loaded from CDNs): MapLibre GL JS 4.7, Plotly 2.35, Font Awesome 6.

## Licence and citation

Code: MIT (see `../LICENSE`). Model output in `data/`: for demonstration only.

Garção, H. (2026). *Coastal Currents Demo — Vitória Bay*. https://hgarcao.github.io/cv_web/portfolio.html
