# Arabian Gulf Wave Demo (SWAN, 0.1°)

Interactive viewer for the output of a SWAN wave model over the Arabian Gulf: significant wave height (Hs),
peak period (Tp) and wave direction, with a time slider and a time series for any clicked point.

The demo is **static**: it reads one pre-computed file from `data/`. It does not run the model.

## Run locally

```bash
python -m http.server 8080
```

from the repository root, then open <http://localhost:8080/demo-waves/>. Opening `index.html` as a plain file does not work.

## Data

| File | Content |
|---|---|
| `data/meta.json` | times (121 hourly outputs, 2024-08-26 00:00 to 2024-08-31 00:00 UTC), grid coordinates (97 × 67, 0.1°), value ranges |
| `data/waves.bin.gz` | Hs, Tp, mean direction and peak direction as int16, layout `[variable][time][lat][lon]` (see `tools/build_wave_data.py`) |

`tools/build_wave_data.py` shows how the files were made from the SWAN NetCDF output (not included).

## Notes

- Directions are nautical (direction the waves come from); animated particles drift in the direction of propagation at uniform speed; the colour underneath shows Hs or Tp.
- A personal development project; the results were not used operationally. No comparison with measurements is included.
- Base maps: CARTO and OpenStreetMap contributors. Libraries: MapLibre GL JS 4.7, Plotly 2.35.

Code: MIT (see `../LICENSE`). Data: for demonstration only.
