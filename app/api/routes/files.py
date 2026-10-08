from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.models.schemas import FileInfo, MeasurementResponse
from app.services.file_service import FileProcessingError, file_service
from app.utils.validation import validate_upload

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/", response_model=FileInfo, status_code=status.HTTP_201_CREATED)
async def upload_file(file: UploadFile = File(...)) -> FileInfo:
    content = await validate_upload(file)
    try:
        return file_service.process_upload(file.filename or "upload", content)
    except (FileProcessingError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Unexpected error while processing file.") from exc


@router.get("/{file_id}/", response_model=FileInfo)
def get_file_info(file_id: str) -> FileInfo:
    info = file_service.get_file(file_id)
    if info is None:
        raise HTTPException(status_code=404, detail="File not found.")
    return info


@router.get("/{file_id}/measurements/", response_model=MeasurementResponse)
def get_measurements(file_id: str) -> MeasurementResponse:
    info = file_service.get_file(file_id)
    if info is None:
        raise HTTPException(status_code=404, detail="File not found.")

    cached = file_service.get_measurements(file_id)
    if cached is None:
        raise HTTPException(status_code=409, detail="Measurements are not available.")

    features, measurement_crs = cached
    return MeasurementResponse(
        file_id=file_id,
        crs=info.crs,
        measurement_crs=measurement_crs,
        features=features,
    )
