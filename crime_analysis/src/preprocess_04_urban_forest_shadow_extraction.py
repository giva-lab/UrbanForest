# Auto-extracted from 04_urban_forest_shadow_extraction.ipynb


# ---- notebook cell 0 ----
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# =========================================================
# 1. Ler dataset completo
# =========================================================

df = pd.read_csv(
    "all_26_districts.csv",
    sep=';'
)

print(df.shape)
print(df["PREDICTED"].value_counts())

# =========================================================
# 2. Separar vegetação urbana
# =========================================================

df_veg = df.loc[
    df["PREDICTED"].eq("VEG")
].copy()

# =========================================================
# 3. Separar sombras
# =========================================================

df_shadow = df.loc[
    df["PREDICTED"].eq("SHADOWS")
].copy()

print("VEG:", df_veg.shape)
print("SHADOWS:", df_shadow.shape)

# =========================================================
# 4. Função para converter em GeoPackage
# =========================================================

def create_gpkg(df_input, output_name):

    geometry = [
        Point(xy)
        for xy in zip(df_input["LONG"], df_input["LAT"])
    ]

    gdf = gpd.GeoDataFrame(
        df_input,
        geometry=geometry,
        crs="EPSG:4326"
    )

    # Reprojetar para SIRGAS 2000 / UTM 23S
    gdf = gdf.to_crs("EPSG:31983")

    # Exportar
    gdf.to_file(
        output_name,
        driver="GPKG"
    )

    print(output_name)
    print(gdf.shape)
    print(gdf.crs)

    return gdf

# =========================================================
# 5. Exportar vegetação
# =========================================================

gdf_veg = create_gpkg(
    df_veg,
    "urban_forest_points.gpkg"
)

# =========================================================
# 6. Exportar sombras
# =========================================================

gdf_shadow = create_gpkg(
    df_shadow,
    "shadow_points.gpkg"
)
