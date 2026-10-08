from pathlib import Path
from zipfile import ZipFile, BadZipFile


def safe_extract_shapefile(zip_path: Path, destination: Path) -> Path:
    """Safely extract a ZIP and return the directory containing the Shapefile."""
    try:
        with ZipFile(zip_path) as archive:
            members = archive.infolist()
            if not members:
                raise ValueError("ZIP archive is empty.")

            destination_resolved = destination.resolve()
            for member in members:
                member_path = (destination / member.filename).resolve()
                if not str(member_path).startswith(str(destination_resolved)):
                    raise ValueError("ZIP archive contains an unsafe path.")
                if member.is_dir():
                    continue
                archive.extract(member, destination)
    except BadZipFile as exc:
        raise ValueError("Uploaded file is not a valid ZIP archive.") from exc

    shp_files = list(destination.rglob("*.shp"))
    if not shp_files:
        raise ValueError("ZIP archive does not contain a Shapefile (.shp).")
    if len(shp_files) > 1:
        raise ValueError("ZIP archive must contain exactly one Shapefile (.shp).")

    return shp_files[0]
