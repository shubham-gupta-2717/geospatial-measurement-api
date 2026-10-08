# Geospatial File Measurement API

A production-oriented FastAPI backend that accepts **KML** files or **ZIP archives containing a Shapefile**, extracts geospatial features, handles coordinate reference systems safely, and returns area/length measurements.

## Features

- FastAPI REST API
- Upload `.kml` or `.zip` containing one Shapefile
- Extract feature ID/index, geometry type, properties and CRS
- Polygon / MultiPolygon area measurement
- LineString / MultiLineString length measurement
- Point features returned without a measurement
- Graceful handling of unsupported geometry types
- Automatic projected CRS selection for geographic input such as EPSG:4326
- ZIP path-traversal protection
- Upload size and extension validation
- Swagger/OpenAPI documentation
- Pytest test suite
- Docker support

## Tech Stack

- Python 3.12+
- FastAPI
- GeoPandas
- Shapely
- PyProj
- Pydantic
- Pytest
- Uvicorn

## Project Structure

```text
geospatial-measurement-api/
├── app/
│   ├── api/routes/files.py       # HTTP endpoints
│   ├── models/schemas.py         # Pydantic response models
│   ├── services/file_service.py  # Upload + processing orchestration
│   ├── services/crs_service.py  # Projected CRS selection
│   ├── services/measurement_service.py
│   ├── utils/archive.py          # Safe ZIP extraction
│   ├── utils/validation.py       # Upload validation
│   └── main.py
├── tests/
├── data/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Setup

### Option 1: Local Python environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

Start the server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Option 2: Docker

```bash
docker compose up --build
```

## API

### Health check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Upload and process a file

```http
POST /api/files/
Content-Type: multipart/form-data
```

Example with curl:

```bash
curl -X POST "http://localhost:8000/api/files/" \
  -F "file=@./sample/survey.kml"
```

For a Shapefile, upload the complete Shapefile components inside a ZIP archive:

```bash
zip survey.zip survey.shp survey.shx survey.dbf survey.prj
curl -X POST "http://localhost:8000/api/files/" \
  -F "file=@survey.zip"
```

Response:

```json
{
  "id": "8f4a6c21d9ab",
  "filename": "survey.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED"
}
```

### Get file information

```http
GET /api/files/{id}/
```

Example:

```bash
curl "http://localhost:8000/api/files/8f4a6c21d9ab/"
```

### Get measurements

```http
GET /api/files/{id}/measurements/
```

Example response:

```json
{
  "file_id": "8f4a6c21d9ab",
  "crs": "EPSG:4326",
  "measurement_crs": "EPSG:32643",
  "features": [
    {
      "id": 0,
      "geometry_type": "Polygon",
      "properties": {
        "name": "Survey Area"
      },
      "measurement": {
        "type": "area",
        "value": 12543.72,
        "unit": "m²",
        "reason": null
      }
    },
    {
      "id": 1,
      "geometry_type": "LineString",
      "properties": {
        "name": "Road"
      },
      "measurement": {
        "type": "length",
        "value": 842.31,
        "unit": "m",
        "reason": null
      }
    },
    {
      "id": 2,
      "geometry_type": "Point",
      "properties": {
        "name": "Sensor"
      },
      "measurement": null
    }
  ]
}
```

## Architecture

The request flow is:

```text
Client
  |
  v
FastAPI Router
  |
  +--> Upload validation
  |
  +--> ZIP safe extraction (if required)
  |
  +--> GeoPandas reads KML/Shapefile
  |
  +--> Feature + CRS inspection
  |
  +--> Measurement CRS selection
  |
  +--> Geometry measurements
  |
  v
Pydantic response
```

### File processing

1. Validate the extension and maximum upload size.
2. Assign a generated ID to the uploaded file.
3. Store the original upload under `data/files/{id}`.
4. If the upload is a ZIP, safely extract it and require exactly one `.shp` file.
5. Load the geospatial dataset using GeoPandas.
6. Reject empty datasets and malformed files with a client-friendly error.
7. Calculate and cache measurements for the API response.

### Measurement calculation

Polygon and MultiPolygon geometries use their projected `area` in square meters. LineString and MultiLineString geometries use their projected `length` in meters. Point geometries do not require a measurement. Unsupported types produce a structured reason rather than crashing the complete request.

## CRS Handling

Geographic CRSs such as EPSG:4326 express coordinates as longitude/latitude degrees. Area and distance cannot be correctly calculated by directly calling Shapely/GeoPandas measurements on those geometries.

The application therefore:

1. Checks whether the source CRS is projected.
2. If the source CRS is geographic, estimates an appropriate local UTM CRS from the dataset extent.
3. Reprojects the geometries to that CRS.
4. Calculates area or length in metric units.
5. Returns the selected measurement CRS in the API response.

For example, a dataset around Pune may be transformed to the appropriate UTM zone before its measurements are calculated.

If a file has no CRS metadata, the API does not invent one. In a production deployment, such files should either provide a CRS or be rejected/configured explicitly because measurement units cannot be guaranteed without CRS information.

## Design Decisions

### Why FastAPI?

FastAPI provides typed request/response models, automatic OpenAPI documentation, asynchronous file handling, and a lightweight architecture suitable for this service.

### Why GeoPandas?

GeoPandas provides a high-level interface for reading geospatial formats, managing CRS information, and working with Shapely geometries while keeping the implementation concise.

### Why UTM for geographic data?

UTM is a practical local projected CRS for metric measurements over regional datasets. GeoPandas' `estimate_utm_crs()` is used as the first choice instead of hardcoding a CRS for one geographic location.

### Why local storage?

The assignment focuses on API and geospatial processing rather than distributed storage. Local storage keeps the implementation simple. In production, the storage layer can be replaced with S3/GCS/Azure Blob Storage without changing the API contract.

### Why cache measurements?

The current implementation processes the upload once and keeps its parsed measurement results in the service layer, so a subsequent measurements request does not repeat expensive geospatial processing.



## Error Handling

The API returns appropriate HTTP errors for:

- Unsupported extensions
- Empty uploads
- Oversized uploads
- Invalid ZIP files
- ZIP archives without a Shapefile
- ZIP archives with multiple Shapefiles
- Invalid geospatial files
- Empty geospatial datasets
- Unknown file IDs

Unsupported geometry types are represented in the measurement response instead of causing the entire request to fail.

## Testing

Run:

```bash
pytest -q
```

The test suite covers:

- Polygon area calculation
- LineString length calculation
- Geographic CRS transformation
- Point handling
- Unsupported geometry handling
- Upload validation
- Basic API endpoints





## License

This project is intended as a technical assessment submission and learning project.
