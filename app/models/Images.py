from pydantic import BaseModel, Field

class Images(BaseModel):
    filename: str | None = None
    data: int
    owner_id: str