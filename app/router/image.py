from fastapi import APIRouter, Depends, UploadFile, HTTPException, status
from typing import Annotated
from app.dependencies.auth_utils import get_current_active_user
from app.models.Users import User
from app.core.db import users_collection, img_collection
from app.dependencies.image_proc import get_user_complete_db, upload_image_to_db, verify_image_owner
from bson.objectid import ObjectId
from PIL import Image
from io import BytesIO
import datetime
from app.models.Images import ImageInDB, ImageUpdate, ImageFile

router = APIRouter(
    prefix="/image",
    tags = ["image_processing"]
)

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

@router.patch("/resize", response_model=ImageFile)
async def resize_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    size: tuple[int, int] # [width, height]
):
    # verify if the user own the image
    verify_image_owner(User.username, image_id)
    
    # get the image to edit
    stored_image = img_collection.find_one({"_id":ObjectId(image_id)})
    if stored_image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image not found")

    # create ImageInDB model from image data
    stored_image_model = ImageInDB(**stored_image)

    # open the image then resize, also edit the width and height data from database
    with Image.open(BytesIO(stored_image["data"])) as im:
        # buffer to save and read edited image BytesIO data
        img_buffer = BytesIO()
        edited_image = im.resize(size)
        edited_image.save(img_buffer, im.format, quality="keep")
        modified_image_data = ImageUpdate(
            modified_date = datetime.datetime.now(),
            filesize = img_buffer.tell(),
            width = size[0],
            height = size[1],
            data = img_buffer.getvalue()
        )

        updated_image = stored_image_model.model_copy(update=modified_image_data.model_dump(exclude_unset=True))

        # save updated image to database
        img_collection.update_one(
            {"_id":ObjectId(image_id)},
            {"$set":updated_image.model_dump()}
        )
    return updated_image