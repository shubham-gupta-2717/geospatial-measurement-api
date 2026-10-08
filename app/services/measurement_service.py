from typing import Any

import geopandas as gpd
from pyproj import CRS

from app.models.schemas import FeatureMeasurement, Measurement
from app.services.crs_service import select_measurement_crs

SUPPORTED_MEASUREMENT_TYPES = {"Polygon", "MultiPolygon", "LineString", "MultiLineString"}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return str(value)


def calculate_measurements(gdf: gpd.GeoDataFrame) -> tuple[list[FeatureMeasurement], str | None]:
    measurement_crs = select_measurement_crs(gdf)
    projected = gdf.to_crs(measurement_crs) if measurement_crs else gdf
    measurement_crs_text = measurement_crs.to_string() if measurement_crs else None

    results: list[FeatureMeasurement] = []
    for index, (_, original_row) in enumerate(gdf.iterrows()):
        geometry = original_row.geometry
        geometry_type = geometry.geom_type if geometry is not None else "Unknown"
        properties = {
            str(key): _json_safe(value)
            for key, value in original_row.drop(labels=["geometry"]).to_dict().items()
        }

        measurement = None
        projected_geometry = projected.iloc[index].geometry

        if projected_geometry is not None and not projected_geometry.is_empty:
            if geometry_type in {"Polygon", "MultiPolygon"}:
                measurement = Measurement(
                    type="area",
                    value=float(projected_geometry.area),
                    unit="m²",
                )
            elif geometry_type in {"LineString", "MultiLineString"}:
                measurement = Measurement(
                    type="length",
                    value=float(projected_geometry.length),
                    unit="m",
                )
            elif geometry_type == "Point":
                measurement = None
            else:
                measurement = Measurement(
                    reason=f"Measurement is not supported for geometry type '{geometry_type}'."
                )

        results.append(
            FeatureMeasurement(
                id=index,
                geometry_type=geometry_type,
                properties=properties,
                measurement=measurement,
            )
        )

    return results, measurement_crs_text
