# Provenance manifest

Canonical final workflow:

1. `src/audit.py`, `src/models.py`, `src/spatial_cv.py`, `src/verify.py`, and `src/report.py` — deterministic audit/model workflow.
2. `src/spatial_nb_bym_mcmc_confirmatory.py` — final aggregate MCMC spatial sensitivity.
3. `src/spatial_nb_bym_subtypes.py` — final vehicle-theft/vehicle-robbery MCMC spatial sensitivities, including subtype reconstruction from the cleaned crime CSV.
4. `notebooks/` — preserved preprocessing/modeling notebooks used as provenance artifacts.
5. `expected_results/` — manuscript-defining numerical reference outputs.
6. `validation_results/spatial_subtypes_2026-10-11/` — fresh independent subtype MCMC rerun used during final reproducibility validation.

Development attempts based on splines or ADVI are not part of the canonical reported workflow. Some historical ADVI artifacts remain only where preserved as provenance; they must not be interpreted as the manuscript's final spatial model.

No raw or derived research dataset is redistributed in this code archive. See `DATA_REQUIREMENTS.md`.
