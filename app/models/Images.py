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
    width: int
    height: int
    mode: str

class ImageInDB(ImageFile):
    data: Any
    owner_id: Any