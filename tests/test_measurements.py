import geopandas as gpd
from shapely.geometry import LineString, Point, Polygon

from app.services.measurement_service import calculate_measurements


def test_polygon_area_is_calculated_in_projected_crs():
    gdf = gpd.GeoDataFrame(
        {"name": ["square"]},
        geometry=[Polygon([(73.85, 18.50), (73.86, 18.50), (73.86, 18.51), (73.85, 18.51)])],
        crs="EPSG:4326",
    )

    results, measurement_crs = calculate_measurements(gdf)

    assert measurement_crs is not None
    assert results[0].measurement is not None
    assert results[0].measurement.type == "area"
    assert results[0].measurement.unit == "m²"
    assert results[0].measurement.value > 1_000_000


def test_linestring_length_is_calculated_in_meters():
    gdf = gpd.GeoDataFrame(
        {"name": ["road"]},
        geometry=[LineString([(73.85, 18.50), (73.86, 18.50)])],
        crs="EPSG:4326",
    )

    results, measurement_crs = calculate_measurements(gdf)

    assert measurement_crs is not None
    assert results[0].measurement.type == "length"
    assert results[0].measurement.unit == "m"
    assert results[0].measurement.value > 500


def test_point_has_no_measurement():
    gdf = gpd.GeoDataFrame(
        {"name": ["sensor"]},
        geometry=[Point(73.85, 18.50)],
        crs="EPSG:4326",
    )

    results, _ = calculate_measurements(gdf)

    assert results[0].measurement is None


def test_unsupported_geometry_is_handled_gracefully():
    from shapely.geometry import GeometryCollection

    gdf = gpd.GeoDataFrame(
        {"name": ["mixed"]},
        geometry=[GeometryCollection([Point(73.85, 18.50)])],
        crs="EPSG:4326",
    )

    results, _ = calculate_measurements(gdf)

    assert results[0].measurement is not None
    assert "not supported" in results[0].measurement.reason
