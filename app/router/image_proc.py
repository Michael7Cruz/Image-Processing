from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from typing import Annotated
from app.dependencies.auth_utils import get_current_active_user
from app.models.Users import User
from app.core.db import users_collection, img_collection
from app.dependencies.auth_utils import get_user
from pymongo.collection import Collection

router = APIRouter(
    prefix="/imageproc",
    tags = ["image_processing"]
)

def get_user_complete_db(username: str):
    # check user in the database
    user_db = users_collection.find_one({"username":username})
    if user_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user_db

async def upload_image_to_db(img_collection: Collection, user_db: dict, img_file: UploadFile):
    # image file model
    image = {
        "filename": img_file.filename,
        "data": await img_file.read(size=-1),
        "owner_id": user_db["_id"]
    }

    # insert the image to the collection and get the id
    image_id = img_collection.insert_one(image).inserted_id

    # check if there is already an images list field in user_db
    # if there are, then update the list, else add that field
    if "images" in user_db:
        users_collection.update_one({"_id":user_db["_id"]},{"$addToSet":{"images":image_id}})
    else:
        users_collection.update_one({"_id":user_db["_id"]},{"$set":{"images":[image_id]}})

    return img_file.filename

@router.post("/upload")
async def upload_image(
    User: Annotated[User, Depends(get_current_active_user)],
    img_file: UploadFile,
):
    # get user data in collection including id to be passed to the image collection
    user_db = get_user_complete_db(User.username)

    # upload to database
    filename = await upload_image_to_db(img_collection, user_db, img_file)
    
    return {"filename": filename}