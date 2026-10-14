#!/usr/bin/env python3
"""Reproduction dispatcher for the Applied Geography manuscript.

This file does not hide the individual analysis steps: it runs the preserved
source scripts in their documented order. Long Bayesian MCMC stages are opt-in.
"""
from pathlib import Path
import argparse, os, subprocess, sys
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'src'

def run(name,*args):
    cmd=[sys.executable,str(SRC/name),*map(str,args)]
    print('\n>>>',' '.join(cmd),flush=True)
    env=os.environ.copy(); env.setdefault('OPENBLAS_NUM_THREADS','1'); env.setdefault('OMP_NUM_THREADS','1')
    subprocess.run(cmd,cwd=ROOT,env=env,check=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input-dir',default='input',help='Directory containing source data expected by audit.py')
    p.add_argument('--spatial',action='store_true',help='Also run aggregate and subtype Bayesian spatial MCMC (slow)')
    p.add_argument('--skip-report',action='store_true')
    a=p.parse_args()
    run('audit.py',a.input_dir)
    run('models.py')
    run('spatial_cv.py')
    run('verify.py',a.input_dir)
    if not a.skip_report: run('report.py')
    if a.spatial:
        # Spatial scripts expect audit_cells.gpkg in working directory.
        produced=ROOT/'investigation'/'results'/'audit_cells.gpkg'
        target=ROOT/'audit_cells.gpkg'
        if produced.exists() and not target.exists():
            try: target.symlink_to(produced)
            except OSError:
                import shutil; shutil.copy2(produced,target)
        run('spatial_nb_bym_mcmc_confirmatory.py')
        run('spatial_nb_bym_subtypes.py')
    print('\nFinished. Run: python check_expected_results.py')
if __name__=='__main__': main()
