from fastapi import APIRouter, Body, Depends, UploadFile, HTTPException, status
from typing import Annotated
from app.dependencies.auth_utils import get_current_active_user
from app.models.Users import User
from app.core.db import users_collection, img_collection
from bson.objectid import ObjectId
from app.models.Images import ImageInDB, ImageFile
from app.dependencies.image_proc import (
    get_user_complete_db,
    upload_image_to_db, 
    verify_image_owner, 
    get_image_by_id, 
    update_image_resize,
    update_image_crop,
    update_image_rotate,
    update_image_watermark_text, 
)

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
    stored_image = get_image_by_id(image_id)

    # create ImageInDB model from image data
    stored_image_model = ImageInDB(**stored_image)

    # open the image then resize, also edit the width and height data from database
    updated_image = update_image_resize(image_id, size, stored_image, stored_image_model)

    return updated_image

@router.patch("/crop", response_model=ImageFile)
async def crop_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    box: tuple[float, float, float, float] | None = None # left, upper, right, and lower pixel coordinate
):
    # verify if the user own the image
    verify_image_owner(User.username, image_id)

    # get the image to edit
    stored_image = get_image_by_id(image_id)

    # create ImageInDB model from image data
    stored_image_model = ImageInDB(**stored_image)

    # crop the image and update the database
    updated_image = update_image_crop(image_id, box, stored_image, stored_image_model)

    return updated_image

@router.patch("/rotate", response_model=ImageFile)
async def rotate_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    angle: Annotated[float, Body()] # in degrees counter clockwise.
):
    # verify if the user own the image
    verify_image_owner(User.username, image_id)

    # get the image to edit
    stored_image = get_image_by_id(image_id)

    # create ImageInDB model from image data
    stored_image_model = ImageInDB(**stored_image)

    # crop the image and update the database
    updated_image = update_image_rotate(image_id, angle, stored_image, stored_image_model)

    return updated_image

@router.patch("/watermark_text", response_model=ImageFile)
async def watermark_text(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    xy: Annotated[tuple[float, float], Body()],
    fill_color: Annotated[tuple[int, int, int, int], Body()] = (255, 255, 255, 128),
    text_watermark: Annotated[str, Body()] = "sample watermark",
    font_type: Annotated[str, Body()] = "arial.ttf",
    font_size: Annotated[float, Body()] = 10.0
):
    # verify if the user own the image
    verify_image_owner(User.username, image_id)

    # get the image to edit
    stored_image = get_image_by_id(image_id)

    # create ImageInDB model from image data
    stored_image_model = ImageInDB(**stored_image)

    # crop the image and update the database
    updated_image = update_image_watermark_text(
        image_id, 
        xy, 
        fill_color, 
        text_watermark, 
        font_type, 
        font_size,
        stored_image, 
        stored_image_model
    )

    return updated_image