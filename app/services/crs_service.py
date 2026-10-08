import math

import geopandas as gpd
from pyproj import CRS


def select_measurement_crs(gdf: gpd.GeoDataFrame) -> CRS | None:
    """Choose a metric projected CRS appropriate for the dataset extent."""
    if gdf.crs is None:
        return None

    source_crs = CRS.from_user_input(gdf.crs)
    if source_crs.is_projected:
        return source_crs

    # GeoPandas' estimate_utm_crs uses dataset bounds and is a good default
    # for local/regional measurements in geographic coordinate systems.
    try:
        estimated = gdf.estimate_utm_crs()
        if estimated is not None:
            return CRS.from_user_input(estimated)
    except (RuntimeError, ValueError):
        pass

    # Fallback for unusual global datasets: choose a UTM zone from centroid.
    geographic = gdf.to_crs("EPSG:4326")
    centroid = geographic.geometry.union_all().centroid
    lon = max(-180.0, min(180.0, centroid.x))
    lat = max(-80.0, min(84.0, centroid.y))
    zone = int(math.floor((lon + 180) / 6) + 1)
    zone = max(1, min(60, zone))
    epsg = 32600 + zone if lat >= 0 else 32700 + zone
    return CRS.from_epsg(epsg)
