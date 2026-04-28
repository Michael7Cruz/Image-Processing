import io
from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from typing import Annotated
from app.dependencies.auth_utils import get_current_active_user
from app.models.Users import User
from app.core.db import users_collection, img_collection

router = APIRouter(
    prefix="/imageproc",
    tags = ["image_processing"]
)

@router.post("/upload")
async def upload_image(
    User: Annotated[User, Depends(get_current_active_user)],
    img_file: UploadFile,
):
    # check user in the database
    user_db = users_collection.find_one({"username":User.username})
    if user_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # image file model
    image = {
        "filename": img_file.filename,
        "data": await img_file.read(size=-1),
        "owner_id": user_db["_id"]
    }

    # insert the image to the collection and get the id
    image_id = img_collection.insert_one(image).inserted_id

    # check if there is already an images list field in user_db
    # if there are then update the list, else add that field
    if "images" in user_db:
        users_collection.update_one({"_id":user_db["_id"]},{"$addToSet":{"images":image_id}})
    else:
        users_collection.update_one({"_id":user_db["_id"]},{"$set":{"images":[image_id]}})
    
    return {"filename": img_file.filename}