# UrbanForest

Repository hosting the datasets generated for the article **"Generating Urban Forest Datasets from Satellite Imagery: Application to the City of São Paulo"**.  
Data were produced using CBERS-4A imagery and open-source tools, providing accurate and reproducible information on urban green cover distribution.

## 🔬 Additional Research

This repository also hosts the reproducibility materials for the manuscript:

**"Fine-Scale Spatial Associations Between Urban Vegetation, Shadow Coverage, and Property Crime in São Paulo"**

The complete analysis code, expected results, validation outputs, computational environment requirements, and reproducibility documentation are available in:

➡️ [`crime_analysis/`](crime_analysis/)

The crime analysis investigates fine-scale spatial associations between urban vegetation, shadow coverage, and property crime across central districts of São Paulo. The repository includes the frequentist analyses and the spatial negative-binomial sensitivity models used in the manuscript.

Third-party source data required for full reproduction are not redistributed in this repository. Instructions describing the required input files and their placement are provided in the `crime_analysis` documentation.

## 📂 Repository Structure

- `data/` → Main dataset files (CSV files with urban forest information)
- `docs/` → Documentation and metadata description
- `crime_analysis/` → Reproducibility materials for the crime, vegetation, and shadow analysis
- `README.md` → Overview of the repository
- `LICENSE` → License for dataset use

## 📂 Contents

- Urban forest datasets in CSV format
- Metadata description files (to explain dataset columns and structure)
- Reproducibility code and validation materials for the crime, vegetation, and shadow analysis

## 📖 Citation

If you use the Urban Forest dataset, please cite:

> Normando Amazonas, Rogério Negri, and Luis Gustavo Nonato. “Generating Urban Forest
> Datasets from Satellite Imagery: Application to the City of São Paulo”. In: Conf. on Graphics, Patterns and Images (SIBGRAPI). 2025, pp. 1–6.

The manuscript associated with the `crime_analysis/` materials is:

> Normando Amazonas, Rogério Negri, and Luis Gustavo Nonato. “Fine-Scale Spatial Associations Between Urban Vegetation, Shadow Coverage, and Property Crime in São Paulo”. Manuscript.

## 📜 License

The Urban Forest dataset is released under the [Creative Commons Zero v1.0 Universal (CC0 1.0)](https://creativecommons.org/publicdomain/zero/1.0/) license.

**Note:** While CC0 allows free use, sharing, and modification without restriction, we recommend citing the corresponding article when using the datasets.

Third-party source data used in the crime analysis are subject to the terms and conditions of their respective data providers and are not redistributed as part of the reproducibility materials.

## 📬 Contact

For questions regarding the datasets, reproducibility materials, or associated research, please contact:

- **Normando Amazonas** – University of São Paulo (USP), ICMC – normandoamazonas@usp.br
- **Prof. Dr. Rogério Negri** – São Paulo State University (UNESP), ICT – rogerio.negri@unesp.br
- **Prof. Dr. Luis Gustavo Nonato** – University of São Paulo (USP), ICMC – gnonato@icmc.usp.br
