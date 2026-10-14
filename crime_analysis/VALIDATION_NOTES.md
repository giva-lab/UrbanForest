# Final validation notes (2026-10-11)

The deterministic workflow was rerun in a clean Python 3.12 environment using `requirements-frequentist.txt`. The manuscript-defining main NB2 model reproduced to floating-point precision (AIC differences on the order of 1e-11; coefficient/result differences negligible), as did Moran's I and spatial cross-validation outputs.

The aggregate Bayesian MCMC was rerun in a separate Python 3.12 spatial environment. It completed with zero divergences and reproduced the manuscript interpretation; the final reduced-posterior NetCDF serialization encountered an ArviZ/xarray compatibility issue only after numerical summaries had been saved. The serialization code in this package has been updated to use `xarray.Dataset.to_netcdf` directly; this change affects output serialization only, not model inference.

The subtype Bayesian MCMC was rerun completely on 2026-10-11. It reconstructed 12,172 thefts and 2,533 robberies with zero cell-level mismatches, completed with zero divergences, and reproduced the manuscript interpretation. Fresh summary outputs are in `validation_results/spatial_subtypes_2026-10-11/`.

The deterministic runner/verification interface was also corrected so that `--input-dir` is honored consistently by both `audit.py` and `verify.py`. `fase9.qgz`, which is required for QGIS metadata auditing, is now explicitly documented in `DATA_REQUIREMENTS.md`.
