from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FileStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FileInfo(BaseModel):
    id: str
    filename: str
    feature_count: int = Field(ge=0)
    crs: str | None = None
    status: FileStatus


class Measurement(BaseModel):
    type: str | None = None
    value: float | None = None
    unit: str | None = None
    reason: str | None = None


class FeatureMeasurement(BaseModel):
    id: int
    geometry_type: str
    properties: dict[str, Any]
    measurement: Measurement | None


class MeasurementResponse(BaseModel):
    file_id: str
    crs: str | None
    measurement_crs: str | None
    features: list[FeatureMeasurement]
