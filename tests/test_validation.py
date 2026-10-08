import io

import pytest
from fastapi import UploadFile

from app.utils.validation import validate_upload


@pytest.mark.asyncio
async def test_rejects_unsupported_extension():
    upload = UploadFile(filename="test.txt", file=io.BytesIO(b"hello"))
    with pytest.raises(Exception) as exc_info:
        await validate_upload(upload)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_accepts_kml():
    upload = UploadFile(filename="test.kml", file=io.BytesIO(b"<kml/>"))
    assert await validate_upload(upload) == b"<kml/>"
