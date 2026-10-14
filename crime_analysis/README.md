# Reproducibility package — Applied Geography manuscript

Code and supporting reproducibility materials for **“Fine-Scale Spatial Associations Between Urban Vegetation, Shadow Coverage, and Property Crime in São Paulo.”**

## Scope

This repository reproduces the analytical pipeline reported in the manuscript. It excludes abandoned spline and ADVI-only experiments from the canonical workflow. The reported spatial sensitivity model is a **BYM-type 1-km block spatial random-effects negative-binomial model with cell-level outcomes**, not a cell-level BYM2 model. All analyses are observational and should not be interpreted causally.

## Repository structure

- `src/audit.py` — spatial/sample audit and construction of `audit_cells.gpkg`.
- `src/models.py` — main count models, block-based uncertainty, correlations and model outputs.
- `src/spatial_cv.py` — spatial cross-validation.
- `src/verify.py` — deterministic integrity/model checks.
- `src/report.py` — technical report generation.
- `src/spatial_nb_bym_mcmc_confirmatory.py` — aggregate vehicle-crime MCMC spatial sensitivity.
- `src/spatial_nb_bym_subtypes.py` — vehicle-theft/robbery MCMC spatial sensitivities.
- `src/preprocess_*.py` and `notebooks/preprocessing/` — preserved preprocessing code/notebooks.
- `notebooks/modeling/` — preserved modeling/diagnostic notebooks.
- `expected_results/` — manuscript-defining reference outputs.
- `validation_results/spatial_subtypes_2026-10-11/` — independent rerun of the final subtype MCMC used to validate reproducibility.
- `provenance/` — historical provenance material.
- `DATA_REQUIREMENTS.md` — exact local input filenames and data-availability notes.

## Data availability

Source data are intentionally **not bundled**. Some inputs originate from third-party/public administrative sources and redistribution is subject to provider terms. See `DATA_REQUIREMENTS.md`. Local data/output directories are excluded by `.gitignore`.

## Environments

Use **separate environments** for the deterministic/frequentist and Bayesian spatial stages. This mirrors the environments in which the analyses were validated and avoids binary-version conflicts.

### 1. Deterministic/frequentist environment

```bash
conda create -n applied_geo_repro python=3.12 -y
conda activate applied_geo_repro
python -m pip install -r requirements-frequentist.txt
```

Place the six deterministic inputs listed in `DATA_REQUIREMENTS.md` in `input/`, then run:

```bash
python run_reproduction.py --input-dir input
python check_expected_results.py
```

The workflow writes generated deterministic outputs under `investigation/results/`.

### 2. Bayesian spatial environment

```bash
conda create -n applied_geo_spatial python=3.12 -y
conda activate applied_geo_spatial
python -m pip install -r requirements-spatial.txt
```

The spatial MCMC models are computationally expensive. With `audit_cells.gpkg` and, for subtypes, `vei_sp_2024_clean.csv` in the repository root:

```bash
python src/spatial_nb_bym_mcmc_confirmatory.py
python src/spatial_nb_bym_subtypes.py
```

Alternatively, after the deterministic stage, `python run_reproduction.py --input-dir input --spatial` dispatches both spatial scripts as well.

A warning that `g++` is unavailable may reduce performance but did not prevent the validated Windows/Anaconda runs. Installing a compatible C++ compiler may improve PyTensor performance.

## Manuscript-defining targets

Key deterministic targets are 45,004 complete-case cells; 14,705 vehicle crimes (12,172 thefts and 2,533 robberies); main NB2 vegetation coefficient about −0.0032843; shadow about +0.0045083; NB2 alpha about 4.3284; AIC about 58,786.04; and residual Moran's I about 0.05260 at 70.72 m.

The manuscript's aggregate spatial MCMC reported vegetation −0.000970 (95% posterior interval −0.002623 to 0.000674), shadow +0.004639 (0.002831 to 0.006382), and residual Moran's I 0.03058. Subtype manuscript targets are preserved under `expected_results/spatial_subtypes/`.

An independent subtype rerun on 2026-10-11 produced theft vegetation −0.000673, theft shadow +0.005042, robbery vegetation −0.003282, and robbery shadow +0.001592, with zero divergences in both subtype models. These small differences from the manuscript run are expected Monte Carlo variation and do not change the interpretation. The fresh outputs are preserved in `validation_results/spatial_subtypes_2026-10-11/`.

`python check_expected_results.py` compares fresh deterministic outputs, when present, against the preserved expected outputs using numerical tolerances rather than requiring bit-for-bit floating-point equality.

## Notes on MCMC diagnostics

Posterior summaries can vary slightly across platforms/library versions despite fixed random seeds. In the 2026-10-11 validation rerun, environmental-coefficient split-Rhat values were approximately 1.00 and there were zero divergences. The maximum reported split-Rhat for the theft model (1.0566) came from a scale parameter (`sigma_iid`), not the vegetation or shadow coefficients.

## Historical notebook naming

Some preserved notebooks retain names/variables from earlier project stages. They are kept for provenance. The canonical analytical definitions are those in the final scripts and manuscript.
