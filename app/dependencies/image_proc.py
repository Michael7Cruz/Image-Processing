import datetime
from app.core.db import users_collection
from fastapi import UploadFile, HTTPException, status
from pymongo.collection import Collection
from PIL import Image
from app.models.Images import ImageFile, ImageInDB

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