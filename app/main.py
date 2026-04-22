from fastapi import FastAPI
from app.router import user
from app.core.config import settings

app = FastAPI()

app.include_router(user.router)

@app.get("/")
async def root():
    return {"message": {settings.ACCESS_TOKEN_EXPIRE_MINUTES}}