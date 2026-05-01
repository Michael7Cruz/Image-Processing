import datetime
from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from typing import Annotated
from app.dependencies.auth_utils import get_current_active_user
from app.models.Users import User
from app.models.Images import ImageFile, ImageInDB
from app.core.db import users_collection, img_collection
from pymongo.collection import Collection
from bson.objectid import ObjectId
from PIL import Image

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
    image_bytes = await img_file.read(size=-1)

    with Image.open(img_file.file) as im:
        image_file = ImageFile(
            filename = img_file.filename,
            filesize = img_file.size,
            upload_date = datetime.datetime.now(),
            modified_date = datetime.datetime.now(),
            content_type = img_file.content_type,
            format = im.format,
            width = im.width,
            height = im.height,
            mode = im.mode
        )
    
    image_in_db = ImageInDB(
        **image_file.model_dump(),
        data = image_bytes,
        owner_id = user_db["_id"]
    )

    # insert the image to the collection and get the id
    image_id = img_collection.insert_one(image_in_db.model_dump()).inserted_id

    # check if there is already an images list field in user_db
    # if there are, then update the list, else add that field
    if "images" in user_db:
        users_collection.update_one({"_id":user_db["_id"]},{"$addToSet":{"images":image_id}})
    else:
        users_collection.update_one({"_id":user_db["_id"]},{"$set":{"images":[image_id]}})

    return image_file

@router.post("/upload")
async def upload_image(
    User: Annotated[User, Depends(get_current_active_user)],
    img_file: UploadFile,
):
    # get user data in collection including id to be passed to the image collection
    user_db = get_user_complete_db(User.username)

    # upload to database
    image_out = await upload_image_to_db(img_collection, user_db, img_file)
    
    return image_out

@router.delete("/delete")
async def delete_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str
):
    # try to delete the image_id from the list of images id
    user_image_delete_result = users_collection.update_one({"username":User.username},{"$pull":{"images":ObjectId(image_id)}})
    if user_image_delete_result.modified_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image not found in user images")

    # delete the image from image collection
    result = img_collection.delete_one({"_id": ObjectId(image_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image not found")
    
    return {"successfully deleted image": result.raw_result}

@router.get("/view")
async def read_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str
):
    # verify if the user own the image
    user_db = get_user_complete_db(User.username)
    image_owned_by_user = ObjectId(image_id) in user_db["images"]
    if not image_owned_by_user:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "image is not on the list of user images")
    
    # get the image data from collection (not including ids)
    image = img_collection.find_one(
        {"_id":ObjectId(image_id)},
        {"_id":0,"data":0,"owner_id":0}
    )

    return {"image found": image}

@router.get("/viewall")
async def view_all_images(
    User: Annotated[User, Depends(get_current_active_user)]
):
    user_db = get_user_complete_db(User.username)
    cursor = img_collection.find(
        {"owner_id":user_db["_id"]},
        {"_id":0,"data":0,"owner_id":0},
        max_time_ms= 5000
    )

    images = []
    for image in cursor:
        images.append(image)

    return images