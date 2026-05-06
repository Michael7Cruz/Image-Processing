from pydantic import BaseModel, Field
from typing import Any
import datetime

class ImageFile(BaseModel):
    filename: str | None = None
    filesize: int | None = None
    upload_date: datetime.datetime
    modified_date: datetime.datetime
    content_type: str | None = None
    format: str | None = None
    width: float
    height: float
    mode: str

class ImageInDB(ImageFile):
    data: Any
    owner_id: Any

class ImageUpdate(BaseModel):
    filename: str | None = None
    filesize: int | None = None
    upload_date: datetime.datetime | None = None
    modified_date: datetime.datetime
    content_type: str | None = None
    format: str | None = None
    width: float | None = None
    height: float | None = None
    mode: str | None = None
    data: Any