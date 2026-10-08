from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE


async def validate_upload(file: UploadFile) -> bytes:
    filename = file.filename or ""
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload a .kml file or a .zip containing a Shapefile.",
        )

    content = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)} MB.",
        )
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    return content
