from fastapi import APIRouter, Body, Depends, Response, UploadFile, HTTPException, status
from typing import Annotated
from app.dependencies.auth_utils import get_current_active_user
from app.models.Users import User
from app.core.db import users_collection, img_collection
from bson.objectid import ObjectId
from app.models.Images import ImageFile
from app.dependencies.image_proc import (
    get_stored_image_by_owner,
    get_user_complete_db,
    update_image_compress,
    update_image_convert,
    update_image_filter,
    upload_image_to_db, 
    update_image_resize,
    update_image_crop,
    update_image_rotate,
    update_image_watermark_text, 
    update_image_flip,
    image_download
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
    """
    Upload an image file to the database and associate it with the current user.
    - **img_file**: The image file to upload
    """
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
    """
    Delete an image file from the database and remove its association with the current user.
    - **image_id**: The ID of the image to delete
    """
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
    """
    View an image file associated with the current user from the database.
    - **image_id**: The ID of the image to view
    """
    # exception if image id is invalid
    if not ObjectId.is_valid(image_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid image id")
    # verify if the user own the image
    user_db = get_user_complete_db(User.username)
    image_owned_by_user = ObjectId(image_id) in user_db["images"]
    if not image_owned_by_user:
        raise HTTPException(status_code = status.HTTP_403_FORBIDDEN, detail = "image is not on the list of user images")
    
    # get the image data from collection (not including ids)
    image = img_collection.find_one(
        {"_id":ObjectId(image_id)},
        {"_id":0,"owner_id":0}
    )
    # exception if image is not found
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="image not found")
    
    return Response(
        content=image["data"],
        media_type=image["content_type"],
    )

@router.get("/viewall")
async def view_all_images(
    User: Annotated[User, Depends(get_current_active_user)]
):
    """
    View all image files associated with the current user from the database 
    """
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
    """
    Resize an image file associated with the current user from the database. 
    - **image_id**: The ID of the image to resize
    - **size**: A tuple of two integers representing the new width and height of the image
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

    # open the image then resize, also edit the width and height data from database
    updated_image = update_image_resize(image_id, size, stored_image, stored_image_model)

    return updated_image

@router.patch("/crop", response_model=ImageFile)
async def crop_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    box: tuple[float, float, float, float] | None = None # left, upper, right, and lower pixel coordinate
):
    """
    Crop an image file associated with the current user from the database. 
    - **image_id**: The ID of the image to crop
    - **box**: A tuple of four floats representing the left, upper, right, and lower pixel coordinates of the cropping box
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

    # crop the image and update the database
    updated_image = update_image_crop(image_id, box, stored_image, stored_image_model)

    return updated_image

@router.patch("/rotate", response_model=ImageFile)
async def rotate_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    angle: Annotated[float, Body()] # in degrees counter clockwise.
):
    """
    Rotate an image file associated with the current user from the database. 
    - **image_id**: The ID of the image to rotate
    - **angle**: The angle in degrees to rotate the image counter-clockwise
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

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
    """
    Add a text watermark to an image file associated with the current user from the database.
    - **image_id**: The ID of the image to watermark
    - **xy**: A tuple of two floats representing the x and y coordinates where the watermark will be placed
    - **fill_color**: A tuple of four integers representing the RGBA values for the watermark color
    - **text_watermark**: The text to use as the watermark
    - **font_type**: The font file to use for the watermark
    - **font_size**: The size of the font for the watermark
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

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

@router.patch("/flip", response_model=ImageFile)
async def flip_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    method: Annotated[bool, Body()] # 0 for horizontal flip, 1 for vertical flip
):
    """
    Flip an image file associated with the current user from the database vertically or horizontally.
    - **image_id**: The ID of the image to flip
    - **method**: A boolean indicating the flip method (0 for horizontal, 1 for vertical)
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

    # flip the image and update the database
    updated_image = update_image_flip(image_id, method, stored_image, stored_image_model)

    return updated_image

@router.patch("/compress", response_model=ImageFile)
async def compress_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    qlty: Annotated[int, Body()] # percentage of quality to keep, 0-100
):
    """
    Compress an image file associated with the current user from the database.
    - **image_id**: The ID of the image to compress
    - **qlty**: The percentage of quality to keep, 0-100
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

    # compress the image and update the database
    updated_image = update_image_compress(image_id, qlty, stored_image, stored_image_model)

    return updated_image

@router.patch("/convert", response_model=ImageFile)
async def convert_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    format: Annotated[str | None, Body()] # desired image format
):
    """
    Convert an image file associated with the current user from the database.
    - **image_id**: The ID of the image to convert
    - **format**: The desired image format
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

    # convert the image format and update the database
    updated_image = update_image_convert(image_id, format, stored_image, stored_image_model)

    return updated_image

@router.get("/download")
async def download_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    filepath: str
):
    """
    Download an image file associated with the current user from the database.
    - **image_id**: The ID of the image to download
    - **filepath**: The local filepath where the image should be saved
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

    # download the image
    downloaded_image = await image_download(filepath, stored_image, stored_image_model)

    return downloaded_image

@router.patch("/filter", response_model=ImageFile)
async def grayscale_image(
    User: Annotated[User, Depends(get_current_active_user)],
    image_id: str,
    filter_type: Annotated[str | None, Body()] # desired filter from predefined filters (grayscale, sepia, etc.)
):
    """
    Add filter to an image file associated with the current user from the database. 
    - **image_id**: The ID of the image to apply the filter to
    - **filter_type**: The type of filter to apply (grayscale or sepia)
    """

    stored_image, stored_image_model = get_stored_image_by_owner(User.username, image_id)

    # apply the filter and update the database
    updated_image = update_image_filter(image_id, filter_type, stored_image, stored_image_model)

    return updated_image