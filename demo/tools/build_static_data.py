#!/usr/bin/env python3
"""Build the static data files for the portfolio demo (no server needed).

Reads the model output (dados/merged_resultado.nc, Delft3D FM / UGRID), the water
mask and the ECMWF wind file, and writes compact files to <out>/data:

  meta.json          time steps, bounding box, grid size
  mask.bin.gz        water mask (uint8, R*R)
  step_NNN.bin.gz    int16 [u | v] in mm/s on the R*R regular grid (0 on land)
  series.bin.gz      int16 [cell][step][u, v, water level] on a coarser grid (click -> time series)
  wind.json          ECMWF 10 m wind (coarse grid, all steps)
  station.json       VIRTUAL tide station with SYNTHETIC observations (see note inside)

Usage:  python build_static_data.py <out_dir>
Requires: numpy, scipy, h5py.
"""
import gzip
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import h5py
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) / 'data'
OUT.mkdir(parents=True, exist_ok=True)

R = 300            # same grid as the original app
COARSE = 3         # series grid stride
SCALE = 1000.0     # m/s -> mm/s

nc = h5py.File(HERE / 'dados' / 'merged_resultado.nc', 'r')
x = nc['mesh2d_face_x'][:]
y = nc['mesh2d_face_y'][:]
t_sec = nc['time'][:]
t0 = datetime(2026, 6, 9, tzinfo=timezone.utc)
times = [(t0 + timedelta(seconds=float(s))).strftime('%Y-%m-%dT%H:%M:%SZ') for s in t_sec]
nt = len(times)
mask = np.load(HERE / 'dados' / 'water_mask_250.npy').astype(np.uint8)
assert mask.shape == (R, R)

lon_min, lon_max, lat_min, lat_max = float(x.min()), float(x.max()), float(y.min()), float(y.max())
xi = np.linspace(lon_min, lon_max, R)
yi = np.linspace(lat_min, lat_max, R)
XG, YG = np.meshgrid(xi, yi)
pts = np.column_stack((x, y))

def gz(path, raw):
    with gzip.GzipFile(path, 'wb', compresslevel=9, mtime=0) as f:
        f.write(raw)

def clean(a, fill=0.0):
    a = np.array(a, dtype=np.float64)
    a[a < -900] = np.nan
    return a

# mesh -> grid (one triangulation, reused)
interp = LinearNDInterpolator(pts, np.zeros(len(pts)))
tri = interp.tri
def to_grid(values):
    f = LinearNDInterpolator(tri, values)
    return f(XG, YG)

water = mask.astype(bool)
coarse_idx = np.arange(COARSE // 2, R, COARSE)
cy, cx = np.meshgrid(coarse_idx, coarse_idx, indexing='ij')
cwater = water[cy, cx]
ncell = int(cwater.sum())
series = np.zeros((ncell, nt, 3), dtype=np.int16)

for k in range(nt):
    u = clean(nc['mesh2d_ucx'][k]); v = clean(nc['mesh2d_ucy'][k]); s = clean(nc['mesh2d_s1'][k])
    s = np.where(np.isnan(s), np.nanmedian(s), s)
    u = np.nan_to_num(u); v = np.nan_to_num(v)
    ug = np.where(water, np.nan_to_num(to_grid(u)), 0.0)
    vg = np.where(water, np.nan_to_num(to_grid(v)), 0.0)
    sg = np.where(water, np.nan_to_num(to_grid(s)), 0.0)
    raw = np.concatenate([np.round(ug * SCALE).ravel(), np.round(vg * SCALE).ravel()]).astype('<i2').tobytes()
    gz(OUT / f'step_{k:03d}.bin.gz', raw)
    series[:, k, 0] = np.round(ug[cy, cx][cwater] * SCALE)
    series[:, k, 1] = np.round(vg[cy, cx][cwater] * SCALE)
    series[:, k, 2] = np.round(sg[cy, cx][cwater] * SCALE)
    if k % 20 == 0:
        print('step', k, '/', nt, flush=True)

gz(OUT / 'mask.bin.gz', mask.tobytes())
gz(OUT / 'series.bin.gz', series.astype('<i2').tobytes())

# coarse-cell lookup for the click -> series feature
cell_lon = xi[cx][cwater]
cell_lat = yi[cy][cwater]

# wind
w = h5py.File(HERE / 'dados' / 'merged_ECMWF_wind.nc', 'r')
wt0 = datetime(2026, 6, 9, tzinfo=timezone.utc)
# The merged wind file has overlapping, non-monotonic hours (0..45, 24..45, 24, 36, 39):
# keep the first record of each hour and sort. Coverage ends 2026-06-10 21:00 UTC,
# before the end of the 72 h model window.
wh = [int(h) for h in w['time'][:]]
first = {}
for i, h in enumerate(wh):
    first.setdefault(h, i)
order = sorted(first)
wind = {
    'times': [(wt0 + timedelta(hours=h)).strftime('%Y-%m-%dT%H:%M:%SZ') for h in order],
    'lon': [float(a) for a in w['longitude'][:]],
    'lat': [float(a) for a in w['latitude'][:]],
    'u': np.round(w['u10'][:][[first[h] for h in order]], 2).tolist(),
    'v': np.round(w['v10'][:][[first[h] for h in order]], 2).tolist(),
}
(OUT / 'wind.json').write_text(json.dumps(wind), encoding='utf-8')

# virtual tide station near the model: nearest water cell to the area of interest
ST_LON, ST_LAT = -40.2975, -20.3184
d2 = (cell_lon - ST_LON) ** 2 + (cell_lat - ST_LAT) ** 2
si = int(np.argmin(d2))
st_lon, st_lat = float(cell_lon[si]), float(cell_lat[si])
model_wl = series[si, :, 2].astype(float) / SCALE
tm = np.array([datetime.strptime(t, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).timestamp() for t in times])
t10 = np.arange(tm[0], tm[-1] + 1, 600.0)
mod10 = np.interp(t10, tm, model_wl)
rng = np.random.default_rng(42)
noise = np.zeros_like(t10)
for i in range(1, len(noise)):
    noise[i] = 0.8 * noise[i - 1] + rng.normal(0, 0.012)
obs10 = mod10 + noise - 0.01
station = {
    'name': 'Virtual tide station',
    'synthetic': True,
    'note': 'Synthetic observations generated from the model series plus correlated noise (seeded). Illustrative only; not measured data.',
    'lon': st_lon, 'lat': st_lat,
    'times': [datetime.fromtimestamp(t, tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') for t in t10],
    'observed': np.round(obs10, 3).tolist(),
    'modeled': np.round(mod10, 3).tolist(),
}
(OUT / 'station.json').write_text(json.dumps(station), encoding='utf-8')

meta = {
    'time_steps': times, 'resolution': R, 'coarse': COARSE, 'scale': SCALE,
    'lon_min': lon_min, 'lon_max': lon_max, 'lat_min': lat_min, 'lat_max': lat_max,
    'series_cells': ncell,
    'series_lon': [round(float(a), 5) for a in cell_lon],
    'series_lat': [round(float(a), 5) for a in cell_lat],
    'station': {'lon': st_lon, 'lat': st_lat},
}
(OUT / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
print('done:', nt, 'steps,', ncell, 'series cells')
