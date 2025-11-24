import cloudinary
import cloudinary.uploader
import os
from shared.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

def upload_file(file_obj, object_name: str, content_type=None):
    file_obj.seek(0)
    result = cloudinary.uploader.upload(
        file_obj,
        public_id=os.path.splitext(object_name)[0],
        resource_type="image",
        overwrite=True
    )
    return result.get("secure_url")
