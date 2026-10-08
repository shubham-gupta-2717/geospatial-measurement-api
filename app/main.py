from fastapi import FastAPI

from app.api.routes.files import router as files_router

app = FastAPI(
    title="Geospatial File Measurement API",
    description="Upload KML or zipped Shapefiles and calculate CRS-safe geometry measurements.",
    version="1.0.0",
)

app.include_router(files_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
