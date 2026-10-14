#!/usr/bin/env python3
"""Compare fresh outputs with manuscript-defining reference outputs.

Deterministic outputs are compared with tight numerical tolerances rather than
bit-for-bit equality, because BLAS/platform differences can change the last
few floating-point digits. Bayesian MCMC is stochastic and is reported as a
reference/validation check rather than an exact-equality test.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
EXP=ROOT/'expected_results'
FRESH=ROOT/'investigation'/'results'

FILES=['models.csv','moran.csv','cv.csv','spatial_cv.csv']
RTOL=1e-7
ATOL=1e-8

def compare_csv(a,b):
    ea=pd.read_csv(a); fb=pd.read_csv(b)
    if list(ea.columns)!=list(fb.columns) or ea.shape!=fb.shape:
        return False, f'shape/columns differ: expected {ea.shape}, fresh {fb.shape}'
    problems=[]
    for c in ea.columns:
        if pd.api.types.is_numeric_dtype(ea[c]) and pd.api.types.is_numeric_dtype(fb[c]):
            x=ea[c].to_numpy(float); y=fb[c].to_numpy(float)
            ok=np.isclose(x,y,rtol=RTOL,atol=ATOL,equal_nan=True)
            if not ok.all():
                problems.append(f'{c}: max abs diff={np.nanmax(np.abs(x-y)):.3g}')
        else:
            if not ea[c].fillna('<NA>').astype(str).equals(fb[c].fillna('<NA>').astype(str)):
                problems.append(f'{c}: text values differ')
    return not problems, '; '.join(problems) if problems else 'within tolerance'

print('Deterministic result comparison')
all_ok=True
for name in FILES:
    e=EXP/name; f=FRESH/name
    if not f.exists():
        print(f'  SKIP {name}: fresh output not found (run deterministic workflow first)')
        continue
    ok,msg=compare_csv(e,f); all_ok &= ok
    print(f"  {'PASS' if ok else 'FAIL'} {name}: {msg}")

print('\nManuscript spatial MCMC reference targets')
print('  aggregate vegetation: -0.000970  PI [-0.002623, 0.000674]')
print('  aggregate shadow:      0.004639  PI [ 0.002831, 0.006382]')
print('  aggregate Moran I:     0.03058')
print('  subtype targets: expected_results/spatial_subtypes/')
val=ROOT/'validation_results'/'spatial_subtypes_2026-10-11'/'subtype_spatial_comparison.csv'
if val.exists():
    d=pd.read_csv(val)
    print('\nIndependent subtype MCMC validation rerun (2026-10-11):')
    for _,r in d.iterrows():
        print(f"  {r['outcome']} / {r['parameter']}: mean={r['mean']:.6f}, PI=[{r['q2.5']:.6f}, {r['q97.5']:.6f}], Rhat={r['split_rhat']:.4f}")

if not all_ok:
    raise SystemExit(1)
print('\nChecks completed.')
