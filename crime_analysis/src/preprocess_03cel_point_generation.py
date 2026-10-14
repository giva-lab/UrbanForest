# Auto-extracted from 03cel_point_generation.ipynb


# ---- notebook cell 0 ----
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# =========================================================
# 1. Ler CSV
# =========================================================

df = pd.read_csv(
    "crime_vehicle.csv",
    sep=';',
    encoding='utf-8-sig'
)

# =========================================================
# 2. Criar geometria
# =========================================================

geometry = [
    Point(xy)
    for xy in zip(df["LONGITUDE"], df["LATITUDE"])
]

# =========================================================
# 3. Criar GeoDataFrame
# =========================================================

gdf = gpd.GeoDataFrame(
    df,
    geometry=geometry,
    crs="EPSG:4326"
)

# =========================================================
# 4. Reprojetar para SIRGAS 2000 / UTM 23S
# =========================================================

gdf = gdf.to_crs("EPSG:31983")

# =========================================================
# 5. Exportar GeoPackage
# =========================================================

gdf.to_file(
    "crime_vehicle_points.gpkg",
    driver="GPKG"
)

print(gdf.shape)
print(gdf.crs)
