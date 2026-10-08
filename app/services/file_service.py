import json
import shutil
import tempfile
import uuid
from pathlib import Path

import geopandas as gpd

from app.config import DATA_DIR
from app.models.schemas import FileInfo, FileStatus
from app.services.measurement_service import calculate_measurements
from app.utils.archive import safe_extract_shapefile


class FileProcessingError(Exception):
    pass


class FileService:
    def __init__(self) -> None:
        self._files: dict[str, FileInfo] = {}
        self._measurement_cache: dict[str, tuple[list, str | None]] = {}

    def process_upload(self, filename: str, content: bytes) -> FileInfo:
        file_id = uuid.uuid4().hex[:12]
        extension = Path(filename).suffix.lower()
        storage_dir = DATA_DIR / file_id
        storage_dir.mkdir(parents=True, exist_ok=True)

        try:
            source_path = storage_dir / Path(filename).name
            source_path.write_bytes(content)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                if extension == ".zip":
                    data_path = safe_extract_shapefile(source_path, temp_path)
                else:
                    data_path = source_path

                try:
                    gdf = gpd.read_file(data_path)
                except Exception as exc:
                    raise FileProcessingError(f"Unable to read geospatial file: {exc}") from exc

                if gdf.empty:
                    raise FileProcessingError("The geospatial file contains no features.")

                results, measurement_crs = calculate_measurements(gdf)
                crs_text = gdf.crs.to_string() if gdf.crs else None

                info = FileInfo(
                    id=file_id,
                    filename=filename,
                    feature_count=len(gdf),
                    crs=crs_text,
                    status=FileStatus.COMPLETED,
                )
                self._files[file_id] = info
                self._measurement_cache[file_id] = (results, measurement_crs)
                return info

        except Exception:
            shutil.rmtree(storage_dir, ignore_errors=True)
            raise

    def get_file(self, file_id: str) -> FileInfo | None:
        return self._files.get(file_id)

    def get_measurements(self, file_id: str):
        return self._measurement_cache.get(file_id)


file_service = FileService()
