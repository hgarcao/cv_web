#!/usr/bin/env python3
"""Build the static data for the wave demo from a SWAN NetCDF output (regular grid).

Usage:  python build_wave_data.py <swanrun_output.nc> <out_dir>
Requires: numpy, h5py.

Writes <out_dir>/data/meta.json and <out_dir>/data/waves.bin.gz
  waves.bin.gz = int16 little-endian, layout [var][time][lat][lon], var order:
     0 Hsig   (0.001 m)      1 RTpeak (0.01 s)      2 Dir  (0.1 deg)     3 PkDir (0.1 deg)
  -32768 marks land / no data.
"""
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

src, out = Path(sys.argv[1]), Path(sys.argv[2]) / 'data'
out.mkdir(parents=True, exist_ok=True)
f = h5py.File(src, 'r')

lon = f['longitude'][:].astype(float)
lat = f['latitude'][:].astype(float)
t = f['time'][:]
times = [datetime.fromtimestamp(int(s), tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') for s in t]

SCALES = [('Hsig', 1000.0), ('RTpeak', 100.0), ('Dir', 10.0), ('PkDir', 10.0)]
SENT = -32768
chunks = []
stats = {}
for name, sc in SCALES:
    a = f[name][:].astype(float)
    a[(a < -900) | ~np.isfinite(a)] = np.nan
    stats[name] = [float(np.nanmin(a)), float(np.nanmax(a))]
    q = np.where(np.isnan(a), SENT, np.round(a * sc)).astype('<i2')
    assert q.shape == (len(times), len(lat), len(lon)), q.shape
    chunks.append(q.ravel())
raw = np.concatenate(chunks).tobytes()
with gzip.GzipFile(out / 'waves.bin.gz', 'wb', compresslevel=9, mtime=0) as g:
    g.write(raw)

b = f['bathymetry'][:].astype(float)
b[(b < -900) | ~np.isfinite(b)] = np.nan

meta = {
    'times': times, 'nlon': len(lon), 'nlat': len(lat),
    'lon': [round(float(x), 4) for x in lon], 'lat': [round(float(x), 4) for x in lat],
    'vars': [n for n, _ in SCALES], 'scales': [s for _, s in SCALES], 'sentinel': SENT,
    'stats': stats, 'dir_convention': str(f.attrs.get('Directional_convention', b'nautical').decode()
                                          if isinstance(f.attrs.get('Directional_convention'), bytes)
                                          else f.attrs.get('Directional_convention', 'nautical')),
}
(out / 'meta.json').write_text(json.dumps(meta), encoding='utf-8')
print('steps', len(times), 'grid', len(lon), 'x', len(lat), 'bytes', (out / 'waves.bin.gz').stat().st_size, stats)
