# Data requirements

Source data are **not redistributed** in this repository. To rerun the deterministic audit, create an `input/` directory in the repository root and provide the following project inputs:

- `grid_50_analysis_controls_v2.gpkg`
- `grid_50_model_complete_cases_v2.gpkg`
- `grid_cells_without_street.gpkg`
- `landuse_grid50_final.gpkg`
- `landuse.gpkg`
- `fase9.qgz`

The Bayesian spatial scripts additionally require the derived `audit_cells.gpkg` in the repository root. `run_reproduction.py --spatial` creates/copies this file from the deterministic audit output automatically. The subtype spatial model also requires the cleaned crime file `vei_sp_2024_clean.csv` in the repository root.

The inputs originate from the public or research sources described in the manuscript and project provenance. Redistribution of third-party data is subject to the terms and conditions of the respective providers. Users wishing to reproduce the complete pipeline should obtain the corresponding source data from those providers/project sources and preserve the filenames above.

`fase9.qgz` is used only to audit the QGIS project metadata/source references; it is required by `src/audit.py`.
