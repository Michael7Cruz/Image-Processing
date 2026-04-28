from fastapi import FastAPI
from app.router import user, image_proc
from app.core.config import get_settings

app = FastAPI()

app.include_router(user.router)
app.include_router(image_proc.router)

@app.get("/")
async def root():
    return {"message": {get_settings().ACCESS_TOKEN_EXPIRE_MINUTES}}