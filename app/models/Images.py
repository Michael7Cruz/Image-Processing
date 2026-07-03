from pydantic import BaseModel, Field
from typing import Any
import datetime

# This model is used to define data from uploaded image file that is not requiring binary data.
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

# This model is used to accept image data from the database.
class ImageInDB(ImageFile):
    data: Any
    owner_id: Any

# This model is used to update image data in the database.
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