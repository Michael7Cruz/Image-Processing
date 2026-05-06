import datetime
from app.core.db import users_collection, img_collection
from fastapi import UploadFile, HTTPException, status
from pymongo.collection import Collection
from PIL import Image
from app.models.Images import ImageFile, ImageInDB, ImageUpdate
from bson.objectid import ObjectId
from io import BytesIO

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

def verify_image_owner(user: str, image_id: str):
    # verify if the user own the image
    user_db = get_user_complete_db(user)
    image_owned_by_user = ObjectId(image_id) in user_db["images"]
    if not image_owned_by_user:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "image is not on the list of user images")

# get the image from the database using id
def get_image_by_id(image_id: str):
    stored_image = img_collection.find_one({"_id":ObjectId(image_id)})

    if stored_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image not found")
    
    return stored_image

def update_image_resize(image_id: str, size: tuple[int, int], stored_image: dict, stored_image_model: ImageInDB):
    with Image.open(BytesIO(stored_image["data"])) as im:
        # buffer to save and read edited image BytesIO data
        img_buffer = BytesIO()
        edited_image = im.resize(size)
        # save image to buffer with the original format and same quality
        edited_image.save(img_buffer, im.format, quality="keep")
        modified_image_data = ImageUpdate(
            modified_date = datetime.datetime.now(),
            filesize = img_buffer.tell(),
            width = edited_image.width,
            height = edited_image.height,
            data = img_buffer.getvalue()
        )

        updated_image = stored_image_model.model_copy(update=modified_image_data.model_dump(exclude_unset=True))

        # save updated image to database
        img_collection.update_one(
            {"_id":ObjectId(image_id)},
            {"$set":updated_image.model_dump()}
        )
    
    return updated_image

def update_image_crop(image_id: str, box: tuple[float, float, float, float] | None, stored_image: dict, stored_image_model: ImageInDB):
    with Image.open(BytesIO(stored_image["data"])) as im:
        # buffer to save and read edited image BytesIO data
        img_buffer = BytesIO()
        # check validity of box based on image size
        # The right is (left+width) and lower is (upper+height).
        box_is_valid = box and box[0] >= 0 and box[1] >= 0 and box[0] + box[2] <= im.width and box[1] + box[3] <= im.height
        if box_is_valid:
            edited_image = im.crop(box)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid rectangular region")
        # save image to buffer with the original format and same quality
        edited_image.save(img_buffer, im.format, quality="keep")
        modified_image_data = ImageUpdate(
            modified_date = datetime.datetime.now(),
            filesize = img_buffer.tell(),
            width = edited_image.width,
            height = edited_image.height,
            data = img_buffer.getvalue()
        )

        updated_image = stored_image_model.model_copy(update=modified_image_data.model_dump(exclude_unset=True))

        # save updated image to database
        img_collection.update_one(
            {"_id":ObjectId(image_id)},
            {"$set":updated_image.model_dump()}
        )
    
    return updated_image